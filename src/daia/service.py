"""Coordinator reference implementation. No agent-selectable work or voting API."""
from __future__ import annotations
import json
import secrets
import time
from uuid import uuid4
from .crypto import canonical, digest, digest_bytes, fingerprint, verify
from .policy import Policy, evaluate
from .store import Store
from .verifier import check_factorization

class Denied(ValueError):
    """Invalid, expired, unauthorized, or inconsistent operation."""


def valid_artifact(artifact):
    if not isinstance(artifact, str):
        return False
    try:
        return len(artifact.encode("utf-8")) <= 4096
    except UnicodeEncodeError:
        return False


def new_id():
    return uuid4().hex


def token_hash(token: str):
    return digest_bytes(token.encode("utf-8"))


def load_policy(text: str) -> Policy:
    value = json.loads(text)
    return Policy(value["version"], tuple(value["modes"]), value["min_roots"], value["human_gate"])


class Coordinator:
    def __init__(self, store: Store, clock=time.time):
        self.store, self.clock = store, clock
        with store.connect() as db:
            db.execute("INSERT OR IGNORE INTO metadata VALUES ('network_id', ?)", (new_id(),))
            self.network_id = db.execute("SELECT value FROM metadata WHERE key='network_id'").fetchone()[0]

    def now(self):
        return int(self.clock())

    def _event(self, db, kind, object_id):
        # Private, minimal hash chain. Not an independently witnessed transparency log.
        last = db.execute("SELECT event_hash FROM events ORDER BY sequence DESC LIMIT 1").fetchone()
        previous = last[0] if last else "0" * 64
        doc = {"kind": kind, "object_id": object_id, "at": self.now()}
        event_hash = digest({"previous": previous, "event": doc})
        db.execute("INSERT INTO events(event_json,previous_hash,event_hash) VALUES(?,?,?)",
                   (canonical(doc).decode(), previous, event_hash))

    def invite(self, max_jobs=20, lifetime=86400):
        """OPERATOR ONLY; each invite establishes one admitted contributor root.

        Root independence is an operator assertion, not proof of a unique person.
        No MCP tool or public HTTP endpoint exposes this method.
        """
        if type(max_jobs) is not int or not 0 <= max_jobs <= 10000 or not 60 <= lifetime <= 604800:
            raise Denied("Invalid grant")
        root, token = new_id(), secrets.token_urlsafe(32)
        with self.store.connect() as db:
            db.execute("INSERT INTO contributors(id,token_hash,max_jobs,expires) VALUES(?,?,?,?)",
                       (root, token_hash(token), max_jobs, self.now() + lifetime))
            self._event(db, "contributor_admitted", root)
        return {"root_id": root, "token": token, "expires": self.now() + lifetime}

    def authenticate(self, token):
        if not isinstance(token, str) or len(token) > 256:
            raise Denied("Unauthorized")
        with self.store.connect() as db:
            row = db.execute("SELECT * FROM contributors WHERE token_hash=?", (token_hash(token),)).fetchone()
            if row is None or row["revoked"] or row["expires"] <= self.now():
                raise Denied("Unauthorized")
            return row["id"]

    def _root(self, db, root):
        row = db.execute("SELECT * FROM contributors WHERE id=?", (root,)).fetchone()
        if row is None or row["revoked"] or row["expires"] <= self.now():
            raise Denied("Unauthorized")
        return row

    def challenge(self, root, public):
        fingerprint(public)
        with self.store.connect() as db:
            self._root(db, root)
            db.execute("DELETE FROM challenges WHERE expires<=?", (self.now(),))
            count = db.execute("SELECT count(*) FROM challenges WHERE root_id=? AND used=0", (root,)).fetchone()[0]
            if count >= 5:
                raise Denied("Too many registration challenges")
            cid = new_id()
            doc = {"action": "register", "network_id": self.network_id, "challenge_id": cid,
                   "root_id": root, "public_key": public, "nonce": secrets.token_hex(32),
                   "expires": self.now() + 300}
            db.execute("INSERT INTO challenges(id,root_id,public_key,document,expires) VALUES(?,?,?,?,?)",
                       (cid, root, public, canonical(doc).decode(), doc["expires"]))
            return doc

    def register(self, root, challenge_id, signature):
        with self.store.connect() as db:
            self._root(db, root)
            ch = db.execute("SELECT * FROM challenges WHERE id=? AND root_id=?", (challenge_id, root)).fetchone()
            if ch is None or ch["used"] or ch["expires"] <= self.now():
                raise Denied("Invalid registration challenge")
            if not verify(ch["public_key"], json.loads(ch["document"]), signature):
                raise Denied("Invalid registration signature")
            aid = fingerprint(ch["public_key"])
            existing = db.execute("SELECT * FROM agents WHERE id=?", (aid,)).fetchone()
            if existing and (existing["root_id"] != root or existing["revoked"]):
                raise Denied("Key is unavailable")
            if existing is None:
                n = db.execute("SELECT count(*) FROM agents WHERE root_id=?", (root,)).fetchone()[0]
                if n >= 5:
                    raise Denied("Agent limit reached")
                db.execute("INSERT INTO agents(id,root_id,public_key) VALUES(?,?,?)", (aid, root, ch["public_key"]))
                self._event(db, "agent_registered", aid)
            db.execute("UPDATE challenges SET used=1 WHERE id=?", (challenge_id,))
            return {"agent_id": aid}

    def revoke(self, root):
        """Operator revocation; previously valid signatures remain historical evidence."""
        with self.store.connect() as db:
            db.execute("UPDATE contributors SET revoked=1 WHERE id=?", (root,))
            self._event(db, "contributor_revoked", root)

    def _agent(self, db, root, agent):
        self._root(db, root)
        a = db.execute("SELECT * FROM agents WHERE id=? AND root_id=? AND revoked=0", (agent, root)).fetchone()
        if a is None:
            raise Denied("Unauthorized agent")
        return a

    def seed(self, number=10403, policy=None):
        """OPERATOR ONLY. Only the bounded built-in factorization workload is executable."""
        if type(number) is not int or not 4 <= number <= 10**12:
            raise Denied("Invalid demo number")
        policy = policy or Policy()
        with self.store.connect() as db:
            jid = self._job(db, "produce", None, number, policy)
            self._event(db, "job_admitted", jid)
            return jid

    def _job(self, db, mode, target, number, policy):
        jid = new_id()
        context = {"workload": "factorization-demo-v1", "number": number, "mode": mode,
                   "objective": "Find or verify a nontrivial integer factorization; submit JSON factors.",
                   "data_only": True}
        if mode == "adversarial":
            result = db.execute("SELECT artifact FROM results WHERE id=?", (target,)).fetchone()
            context["candidate_artifact"] = result[0]
        # Reproduction receives premises only, not the candidate's artifact or verdicts.
        chash = digest_bytes(json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())
        db.execute("INSERT INTO jobs(id,mode,target_id,number,policy_json,policy_hash,context_json,context_hash) VALUES(?,?,?,?,?,?,?,?)",
                   (jid, mode, target, number, canonical(policy.document()).decode(), policy.hash,
                    json.dumps(context, ensure_ascii=False), chash))
        return jid

    def _expire(self, db):
        expired = db.execute("SELECT id,job_id FROM assignments WHERE state='leased' AND expires<=?", (self.now(),)).fetchall()
        for a in expired:
            db.execute("UPDATE assignments SET state='expired' WHERE id=?", (a["id"],))
            db.execute("UPDATE jobs SET state='queued' WHERE id=? AND state='leased'", (a["job_id"],))
            self._event(db, "lease_expired", a["id"])

    def _package(self, db, a):
        j = db.execute("SELECT * FROM jobs WHERE id=?", (a["job_id"],)).fetchone()
        return {"assignment_id": a["id"], "job_id": j["id"], "mode": j["mode"],
                "network_id": self.network_id, "nonce": a["nonce"], "expires": a["expires"],
                "hard_deadline": a["hard_deadline"], "context_hash": j["context_hash"],
                "policy_hash": j["policy_hash"], "target_id": j["target_id"],
                "context": json.loads(j["context_json"])}

    def request_work(self, root, agent):
        # No caller-supplied job, candidate, mode, reputation, model, or priority.
        with self.store.connect() as db:
            self._agent(db, root, agent)
            self._expire(db)
            grant = self._root(db, root)
            active = db.execute("SELECT * FROM assignments WHERE root_id=? AND state='leased'", (root,)).fetchone()
            if active:
                if active["agent_id"] != agent:
                    return {"status": "other_agent_has_lease"}
                return self._package(db, active)
            if grant["assigned"] >= grant["max_jobs"] or grant["cooldown_until"] > self.now():
                return {"status": "budget_or_cooldown"}
            eligible = []
            for j in db.execute("SELECT * FROM jobs WHERE state='queued'").fetchall():
                subject = j["target_id"] or j["id"]
                if db.execute("SELECT 1 FROM assignments WHERE subject_id=? AND root_id=?", (subject, root)).fetchone():
                    continue
                if j["target_id"]:
                    result = db.execute("SELECT * FROM results WHERE id=?", (subject,)).fetchone()
                    if result is None or result["root_id"] == root or result["state"] != "in_review":
                        continue
                eligible.append(j)
            if not eligible:
                return {"status": "no_eligible_work"}
            j = secrets.choice(eligible)  # Auditable history, NOT publicly verifiable randomness.
            aid, now = new_id(), self.now()
            db.execute("INSERT INTO assignments(id,job_id,agent_id,root_id,subject_id,nonce,issued,expires,hard_deadline) VALUES(?,?,?,?,?,?,?,?,?)",
                       (aid, j["id"], agent, root, j["target_id"] or j["id"], secrets.token_hex(32), now, now+300, now+1800))
            db.execute("UPDATE contributors SET assigned=assigned+1 WHERE id=?", (root,))
            db.execute("UPDATE jobs SET state='leased' WHERE id=?", (j["id"],))
            self._event(db, "assignment_issued", aid)
            return self._package(db, db.execute("SELECT * FROM assignments WHERE id=?", (aid,)).fetchone())

    def _lease(self, db, root, agent, assignment):
        self._agent(db, root, agent)
        a = db.execute("SELECT * FROM assignments WHERE id=? AND root_id=? AND agent_id=?", (assignment, root, agent)).fetchone()
        if a is None or a["state"] != "leased" or a["expires"] <= self.now():
            raise Denied("Invalid or expired assignment")
        return a

    def heartbeat(self, root, agent, assignment):
        with self.store.connect() as db:
            a = self._lease(db, root, agent, assignment)
            expires = min(self.now()+300, a["hard_deadline"])
            db.execute("UPDATE assignments SET expires=? WHERE id=?", (expires, assignment))
            return {"expires": expires}

    def release(self, root, agent, assignment):
        with self.store.connect() as db:
            a = self._lease(db, root, agent, assignment)
            db.execute("UPDATE assignments SET state='released' WHERE id=?", (assignment,))
            db.execute("UPDATE jobs SET state='queued' WHERE id=?", (a["job_id"],))
            db.execute("UPDATE contributors SET cooldown_until=? WHERE id=?", (self.now()+30, root))
            self._event(db, "assignment_released", assignment)
            return {"status": "released"}

    def envelope(self, root, agent, assignment, artifact, verdict):
        if not valid_artifact(artifact):
            raise Denied("Artifact must be at most 4096 UTF-8 bytes")
        if verdict not in {"candidate", "pass", "fail", "inconclusive"}:
            raise Denied("Invalid verdict")
        with self.store.connect() as db:
            a = self._lease(db, root, agent, assignment)
            return self._envelope(db, a, artifact, verdict)

    def _envelope(self, db, a, artifact, verdict):
        j = db.execute("SELECT * FROM jobs WHERE id=?", (a["job_id"],)).fetchone()
        return {"action": "submit", "network_id": self.network_id, "assignment_id": a["id"],
                "job_id": j["id"], "agent_id": a["agent_id"], "nonce": a["nonce"],
                "mode": j["mode"], "target_id": j["target_id"], "policy_hash": j["policy_hash"],
                "context_hash": j["context_hash"], "artifact_hash": digest_bytes(artifact.encode()),
                "verdict": verdict}

    def submit(self, root, agent, assignment, artifact, verdict, signature):
        if not valid_artifact(artifact) or verdict not in {"candidate","pass","fail","inconclusive"}:
            raise Denied("Invalid submission")
        with self.store.connect() as db:
            author = self._agent(db, root, agent)
            a = db.execute("SELECT * FROM assignments WHERE id=? AND root_id=? AND agent_id=?", (assignment, root, agent)).fetchone()
            if a is None:
                raise Denied("Unknown assignment")
            env = self._envelope(db, a, artifact, verdict)
            if not verify(author["public_key"], env, signature):
                raise Denied("Invalid submission signature")
            receipt = digest({"envelope": env, "signature": signature})
            if a["state"] == "submitted" and a["receipt_hash"] == receipt:
                return {"receipt_hash": receipt, "status": "already_recorded"}
            self._lease(db, root, agent, assignment)
            j = db.execute("SELECT * FROM jobs WHERE id=?", (a["job_id"],)).fetchone()
            policy = load_policy(j["policy_json"])
            if j["mode"] == "produce":
                if verdict != "candidate":
                    raise Denied("Producer must submit a candidate")
                result_id = digest({"job_id": j["id"], "artifact_hash": env["artifact_hash"], "policy_hash": policy.hash})
                checked = check_factorization(j["number"], artifact)
                state = "in_review" if checked else "rejected"
                db.execute("INSERT INTO results VALUES(?,?,?,?,?,?,?,?,?)",
                           (result_id, j["id"], root, artifact, env["artifact_hash"], canonical(env).decode(), signature, int(checked), state))
                if checked:
                    for mode in policy.modes:
                        self._job(db, mode, result_id, j["number"], policy)
            else:
                result_id = j["target_id"]
                if verdict == "candidate":
                    raise Denied("Reviewer cannot submit a producer candidate")
                # A reproducer's PASS needs its OWN independently checked certificate.
                if j["mode"] == "reproduce" and verdict == "pass" and not check_factorization(j["number"], artifact):
                    raise Denied("Reproduction certificate failed")
                if not artifact.strip():
                    raise Denied("Review needs evidence or an explanation")
                db.execute("INSERT INTO reviews VALUES(?,?,?,?,?,?,?,?,?,?)",
                           (new_id(), result_id, assignment, root, agent, j["mode"], verdict,
                            artifact, canonical(env).decode(), signature))
                result = db.execute("SELECT * FROM results WHERE id=?", (result_id,)).fetchone()
                reviews = [dict(r) for r in db.execute("SELECT * FROM reviews WHERE result_id=?", (result_id,))]
                state = evaluate(policy, bool(result["machine_check"]), reviews)
                db.execute("UPDATE results SET state=? WHERE id=?", (state, result_id))
            db.execute("UPDATE assignments SET state='submitted',receipt_hash=? WHERE id=?", (receipt, assignment))
            db.execute("UPDATE jobs SET state='completed' WHERE id=?", (j["id"],))
            self._event(db, "submission_recorded", receipt)
            return {"receipt_hash": receipt, "result_id": result_id, "status": state}

    def metrics(self):
        """Only aggregates. No identities, artifacts, prompts, signatures, or tokens."""
        with self.store.connect() as db:
            return {"jobs": db.execute("SELECT count(*) FROM jobs").fetchone()[0],
                    "results": db.execute("SELECT count(*) FROM results").fetchone()[0],
                    "promoted": db.execute("SELECT count(*) FROM results WHERE state='promoted'").fetchone()[0]}
