"""SQLite reference store: serialized writes, durable leases, no distributed claims.

The store intentionally uses BEGIN IMMEDIATE for every operation. It is a local
prototype, not a multi-region coordinator. See docs/postgres.md for the production
transaction model. Never put this database on a shared network filesystem.
"""
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import os

SCHEMA = """
CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS contributors (
 id TEXT PRIMARY KEY, token_hash TEXT NOT NULL UNIQUE,
 max_jobs INTEGER NOT NULL CHECK(max_jobs >= 0),
 assigned INTEGER NOT NULL DEFAULT 0 CHECK(assigned >= 0),
 expires INTEGER NOT NULL, revoked INTEGER NOT NULL DEFAULT 0,
 cooldown_until INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS challenges (
 id TEXT PRIMARY KEY, root_id TEXT NOT NULL REFERENCES contributors(id),
 public_key TEXT NOT NULL, document TEXT NOT NULL, expires INTEGER NOT NULL,
 used INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS agents (
 id TEXT PRIMARY KEY, root_id TEXT NOT NULL REFERENCES contributors(id),
 public_key TEXT NOT NULL UNIQUE, revoked INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS jobs (
 id TEXT PRIMARY KEY, mode TEXT NOT NULL,
 target_id TEXT, number INTEGER NOT NULL,
 policy_json TEXT NOT NULL, policy_hash TEXT NOT NULL,
 context_json TEXT NOT NULL, context_hash TEXT NOT NULL,
 state TEXT NOT NULL DEFAULT 'queued'
);
CREATE TABLE IF NOT EXISTS assignments (
 id TEXT PRIMARY KEY, job_id TEXT NOT NULL REFERENCES jobs(id),
 agent_id TEXT NOT NULL REFERENCES agents(id),
 root_id TEXT NOT NULL REFERENCES contributors(id),
 subject_id TEXT NOT NULL, nonce TEXT NOT NULL,
 issued INTEGER NOT NULL, expires INTEGER NOT NULL, hard_deadline INTEGER NOT NULL,
 state TEXT NOT NULL DEFAULT 'leased', receipt_hash TEXT,
 UNIQUE(subject_id, root_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS one_live_job
 ON assignments(job_id) WHERE state='leased';
CREATE UNIQUE INDEX IF NOT EXISTS one_live_contributor
 ON assignments(root_id) WHERE state='leased';
CREATE TABLE IF NOT EXISTS results (
 id TEXT PRIMARY KEY, job_id TEXT NOT NULL REFERENCES jobs(id),
 root_id TEXT NOT NULL REFERENCES contributors(id), artifact TEXT NOT NULL,
 artifact_hash TEXT NOT NULL, envelope_json TEXT NOT NULL, signature TEXT NOT NULL,
 machine_check INTEGER NOT NULL, state TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reviews (
 id TEXT PRIMARY KEY, result_id TEXT NOT NULL REFERENCES results(id),
 assignment_id TEXT NOT NULL UNIQUE REFERENCES assignments(id),
 root_id TEXT NOT NULL REFERENCES contributors(id), agent_id TEXT NOT NULL REFERENCES agents(id),
 mode TEXT NOT NULL, verdict TEXT NOT NULL, evidence TEXT NOT NULL,
 envelope_json TEXT NOT NULL, signature TEXT NOT NULL,
 UNIQUE(result_id, root_id)
);
CREATE TABLE IF NOT EXISTS events (
 sequence INTEGER PRIMARY KEY AUTOINCREMENT,
 event_json TEXT NOT NULL, previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL UNIQUE
);
"""

class Store:
    def __init__(self, path: str):
        self.path = path
        target = Path(path)
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if target.is_symlink():
            raise ValueError("Database symlinks are not allowed")
        # Exclusive creation avoids a world-readable first-write window on POSIX.
        # Windows ACLs still need operator review; chmod is not an ACL solution.
        try:
            fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            if os.name == "posix" and target.stat().st_mode & 0o077:
                raise ValueError("Existing database must have private filesystem permissions")
        else:
            os.close(fd)
        with self.connect() as db:
            db.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=10000")
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
