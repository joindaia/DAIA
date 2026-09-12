"""Coordinator reference implementation. No agent-selectable work or voting API."""
from __future__ import annotations
import json
import secrets
import time
from pathlib import PurePosixPath
from uuid import uuid4
from .crypto import canonical, digest, digest_bytes, fingerprint, verify
from .policy import Policy, evaluate
from .store import Store
from .verifier import (check_factorization, check_evidence_packet, EVIDENCE_SCHEMAS,
                       EVIDENCE_SCHEMA_HASHES, EVIDENCE_CHECKER_HASH)

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
            if store.create:
                db.execute("INSERT OR IGNORE INTO metadata VALUES ('network_id', ?)", (new_id(),))
            identity = db.execute("SELECT value FROM metadata WHERE key='network_id'").fetchone()
            if identity is None or not isinstance(identity[0], str) or not identity[0]:
                raise Denied("Expected an initialized coordinator database")
            self.network_id = identity[0]

    def now(self):
        return int(self.clock())

    def _event(self, db, kind, object_id, *, details=None):
        # Private, minimal hash chain. Not an independently witnessed transparency log.
        last = db.execute("SELECT event_hash FROM events ORDER BY sequence DESC LIMIT 1").fetchone()
        previous = last[0] if last else "0" * 64
        doc = {"kind": kind, "object_id": object_id, "at": self.now()}
        if details is not None:
            doc["details"] = details
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

    def extend_grant(self, root, max_jobs, expires, *, dry_run=False):
        """OPERATOR ONLY: explicit finite ceilings on an existing live contributor.

        This neither authorizes local consent nor changes identity, usage or exposure.
        Exact retries are idempotent while the grant remains live and nonrevoked.
        """
        if (type(max_jobs) is not int or not 0 <= max_jobs <= 10000
                or type(expires) is not int or type(dry_run) is not bool):
            raise Denied("Invalid grant extension")
        with self.store.connect() as db:
            now = self.now()
            grant = db.execute("SELECT * FROM contributors WHERE id=?", (root,)).fetchone()
            if (grant is None or grant["revoked"] or grant["expires"] <= now
                    or not now < expires <= now + 604800
                    or max_jobs < max(grant["max_jobs"], grant["assigned"])
                    or expires < grant["expires"]):
                raise Denied("Grant extension refused")
            previous = {"max_jobs": grant["max_jobs"], "expires": grant["expires"]}
            proposed = {"max_jobs": max_jobs, "expires": expires}
            changed = previous != proposed
            result = {"status": "preview" if dry_run else "extended" if changed else "already_extended",
                      "root_id": root, "previous": previous, "proposed": proposed,
                      "assigned": grant["assigned"], "remaining": max_jobs - grant["assigned"],
                      "additional_capacity": max_jobs - grant["max_jobs"],
                      "would_change": changed,
                      "changed": changed and not dry_run,
                      "local_consent_changed": False}
            if dry_run or not changed:
                return result
            db.execute("UPDATE contributors SET max_jobs=?,expires=? WHERE id=?", (max_jobs, expires, root))
            self._event(db, "contributor_grant_extended", root,
                        details={"previous": previous, "proposed": proposed})
            return result

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
            contributor = db.execute("SELECT revoked FROM contributors WHERE id=?", (root,)).fetchone()
            if contributor is None:
                raise Denied("Unknown contributor")
            if contributor["revoked"]:
                return
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

    def admit_evidence(self, document, *, pilot=False):
        """OPERATOR ONLY: one unresolved, immutable, data-only source-analysis campaign."""
        if type(pilot) is not bool:
            raise Denied("Pilot mode must be an explicit boolean")
        if not isinstance(document, dict) or set(document) != {"objective", "baseline_commit", "source"}:
            raise Denied("Expected objective, baseline_commit and one frozen source excerpt")
        source = document["source"]
        if (not isinstance(document["objective"], str) or not 1 <= len(document["objective"].strip()) <= 1000
                or not isinstance(document["baseline_commit"], str) or len(document["baseline_commit"]) != 40
                or any(c not in "0123456789abcdef" for c in document["baseline_commit"])
                or not isinstance(source, dict) or set(source) != {"path", "start_line", "text"}
                or not isinstance(source["path"], str) or not 1 <= len(source["path"]) <= 200
                or type(source["start_line"]) is not int or not 1 <= source["start_line"] <= 1000000
                or not isinstance(source["text"], str) or not 1 <= len(source["text"]) <= 6000):
            raise Denied("Invalid bounded source-analysis context")
        path = PurePosixPath(source["path"])
        if (not path.parts or path.is_absolute() or any(p in {"..", "."} or p.startswith(".") for p in path.parts)
                or "\\" in source["path"] or ":" in source["path"]
                or path.parts[0] not in {"src", "tests", "docs"}):
            raise Denied("Expected a repository-relative source path")
        try:
            source_bytes = source["text"].encode("utf-8")
            json.dumps(document, ensure_ascii=False).encode("utf-8")
        except UnicodeError:
            raise Denied("Context must be valid UTF-8") from None
        context = dict(document, source={**source, "sha256": digest_bytes(source_bytes)},
                       workload="source-evidence-v1", data_only=True, mode="produce",
                       evidence_check="structure-and-source-binding-only",
                       human_disposition_required=True,
                       source_provenance="operator-supplied-frozen-excerpt",
                       schemas=EVIDENCE_SCHEMAS, schema_hashes=EVIDENCE_SCHEMA_HASHES,
                       checker_hash=EVIDENCE_CHECKER_HASH)
        if pilot:
            context.update(review_assurance="pilot-technical-not-independent",
                           shared_ownership_allowed=True, independent_review=False)
        if len(json.dumps(context, ensure_ascii=False).encode("utf-8")) > 10000:
            raise Denied("Context exceeds the source-analysis limit")
        # This NEW policy collects evidence; it cannot promote a correctness or payout claim.
        policy = Policy("source-evidence-pilot-v1" if pilot else "source-evidence-v1", ("adversarial",), 1, True)
        admission = digest({"context_hash": digest_bytes(json.dumps(context, ensure_ascii=False,
                           sort_keys=True, separators=(",", ":")).encode()), "policy_hash": policy.hash})
        with self.store.connect() as db:
            existing = db.execute("SELECT job_id FROM evidence_campaigns WHERE context_hash=?", (admission,)).fetchone()
            if existing:
                return {"status": "already_admitted", "job_id": existing["job_id"]}
            if db.execute("SELECT 1 FROM evidence_campaigns WHERE disposition IS NULL").fetchone():
                return {"status": "campaign_unresolved"}
            job = self._job(db, "produce", None, 0, policy, context=context)
            db.execute("INSERT INTO evidence_campaigns(context_hash,job_id) VALUES(?,?)", (admission, job))
            self._event(db, "evidence_campaign_admitted", job)
            return {"status": "admitted", "job_id": job}

    def inspect_evidence(self):
        """OPERATOR ONLY: private source/evidence inspection, without contributor identities."""
        with self.store.connect() as db:
            self._expire(db)
            campaigns = []
            for row in db.execute("SELECT c.*,j.context_json,j.state AS job_state FROM evidence_campaigns c JOIN jobs j ON c.job_id=j.id"):
                result = db.execute("SELECT id,artifact,state,machine_check FROM results WHERE job_id=?", (row["job_id"],)).fetchone()
                reviews = [] if result is None else [dict(r) for r in db.execute(
                    "SELECT mode,verdict,evidence FROM reviews WHERE result_id=?", (result["id"],))]
                campaigns.append({"job_id": row["job_id"], "job_state": row["job_state"],
                    "context": json.loads(row["context_json"]), "disposition": row["disposition"],
                    "disposition_note": row["disposition_note"],
                    "result": None if result is None else {"artifact": result["artifact"],
                        "state": result["state"], "shape_valid": bool(result["machine_check"]),
                        "correctness_verified": False}, "reviews": reviews})
            return campaigns

    def resolve_evidence(self, job, disposition, note, *, dry_run=False):
        """HUMAN OPERATOR ONLY: disposition is evidence triage, never merge or payout authority."""
        if disposition not in {"useful", "duplicate", "unclear", "rejected", "cancelled"} or not isinstance(note, str) or not 1 <= len(note.strip()) <= 2000:
            raise Denied("Provide a bounded human disposition and explanation")
        with self.store.connect() as db:
            campaign = db.execute("SELECT * FROM evidence_campaigns WHERE job_id=?", (job,)).fetchone()
            if campaign is None:
                raise Denied("Unknown evidence campaign")
            if campaign["disposition"] is not None:
                if campaign["disposition"] == disposition and campaign["disposition_note"] == note:
                    if not dry_run:
                        return {"status": "already_resolved"}
                else:
                    raise Denied("A recorded disposition cannot be overwritten")
            result = db.execute("SELECT id,state FROM results WHERE job_id=?", (job,)).fetchone()
            policy = load_policy(db.execute("SELECT policy_json FROM jobs WHERE id=?", (job,)).fetchone()[0])
            ready = "pilot_ready_for_maintainer" if policy.version == "source-evidence-pilot-v1" else "ready_for_maintainer"
            if campaign["disposition"] is None and disposition == "useful" and (result is None or result["state"] != ready):
                raise Denied("Useful disposition requires the assigned review first")
            jobs = [job] + ([] if result is None else [r[0] for r in db.execute("SELECT id FROM jobs WHERE target_id=?", (result["id"],))])
            if dry_run:
                already_resolved = campaign["disposition"] is not None
                return {"status": "preview", "outcome": "already_resolved" if already_resolved else "resolved",
                    "proposal": {"job_id": job, "disposition": disposition, "note": note},
                    "result_state": None if result is None else result["state"],
                    "reviews": [] if result is None else [dict(r) for r in db.execute(
                        "SELECT mode,verdict FROM reviews WHERE result_id=?", (result["id"],))],
                    "effects": {
                        "jobs_to_cancel": 0 if already_resolved else sum(db.execute(
                            "SELECT count(*) FROM jobs WHERE id=? AND state IN ('queued','leased')", (jid,)).fetchone()[0] for jid in jobs),
                        "recorded_leases_to_cancel": 0 if already_resolved else sum(db.execute(
                            "SELECT count(*) FROM assignments WHERE job_id=? AND state='leased'", (jid,)).fetchone()[0] for jid in jobs),
                        "new_terminal_decision": not already_resolved},
                    "correctness_verified": False, "approval_recorded": False,
                    "advisory": "Snapshot only; no state reserved. Recheck effects before applying. Terminal decisions are immutable."}
            db.execute("UPDATE evidence_campaigns SET disposition=?,disposition_note=?,resolved_at=? WHERE job_id=?",
                       (disposition, note, self.now(), job))
            for jid in jobs:
                db.execute("UPDATE assignments SET state='cancelled' WHERE job_id=? AND state='leased'", (jid,))
                db.execute("UPDATE jobs SET state='cancelled' WHERE id=? AND state IN ('queued','leased')", (jid,))
            self._event(db, "evidence_campaign_resolved", job)
            return {"status": "resolved", "disposition": disposition}

    def _job(self, db, mode, target, number, policy, context=None):
        jid = new_id()
        context = dict(context, mode=mode) if context else {"workload": "factorization-demo-v1", "number": number, "mode": mode,
                   "objective": "Find or verify a nontrivial integer factorization; submit JSON factors.",
                   "data_only": True}
        if mode == "adversarial":
            result = db.execute("SELECT artifact FROM results WHERE id=?", (target,)).fetchone()
            context["candidate_artifact"] = result[0]
            if context.get("workload") == "source-evidence-v1":
                context["candidate_digest"] = digest_bytes(result[0].encode("utf-8"))
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
                    pilot = load_policy(j["policy_json"]).version == "source-evidence-pilot-v1"
                    if result is None or (not pilot and result["root_id"] == root) or result["state"] != "in_review":
                        continue
                    # A released/expired producer has already seen the premises. Its
                    # exposure was recorded under the producer job, not this result ID.
                    # Pilot permits another agent of the same owner, not the producer
                    # agent itself. Review exposure above remains root-scoped after release.
                    identity_column, identity = ("agent_id", agent) if pilot else ("root_id", root)
                    if db.execute(f"SELECT 1 FROM assignments WHERE job_id=? AND {identity_column}=?",
                                  (result["job_id"], identity)).fetchone():
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
                context = json.loads(j["context_json"])
                evidence_only = context.get("workload") == "source-evidence-v1"
                checked = check_evidence_packet(context, artifact) if evidence_only else check_factorization(j["number"], artifact)
                state = "in_review" if checked else "rejected"
                db.execute("INSERT INTO results VALUES(?,?,?,?,?,?,?,?,?)",
                           (result_id, j["id"], root, artifact, env["artifact_hash"], canonical(env).decode(), signature, int(checked), state))
                if checked:
                    for mode in policy.modes:
                        self._job(db, mode, result_id, j["number"], policy,
                                  context=context if evidence_only else None)
            else:
                result_id = j["target_id"]
                if verdict == "candidate":
                    raise Denied("Reviewer cannot submit a producer candidate")
                context = json.loads(j["context_json"])
                if context.get("workload") == "source-evidence-v1" and not check_evidence_packet(context, artifact, verdict):
                    raise Denied("Review must be a source-bound evidence packet, including for uncertainty or disagreement")
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
                if policy.version == "source-evidence-pilot-v1" and state == "ready_for_maintainer":
                    state = "pilot_ready_for_maintainer"
                db.execute("UPDATE results SET state=? WHERE id=?", (state, result_id))
            db.execute("UPDATE assignments SET state='submitted',receipt_hash=? WHERE id=?", (receipt, assignment))
            db.execute("UPDATE jobs SET state='completed' WHERE id=?", (j["id"],))
            self._event(db, "submission_recorded", receipt)
            return {"receipt_hash": receipt, "result_id": result_id, "status": state}

    def contribution_status(self, root, agent, migration_check=False, *, expire=True):
        """Own grant and recoverable lease only; never reveals other contributors."""
        with self.store.connect() as db:
            self._agent(db, root, agent)
            if expire:
                self._expire(db)
            grant = self._root(db, root)
            active = db.execute("SELECT * FROM assignments WHERE root_id=? AND state='leased'", (root,)).fetchone()
            history = {}
            if migration_check:
                # Only this contributor's durable history, never other roots' records.
                own = {table: [dict(row) for row in db.execute(
                    f"SELECT * FROM {table} WHERE root_id=? ORDER BY id", (root,))]
                    for table in ("agents", "assignments", "results", "reviews")}
                own["jobs"] = [dict(row) for row in db.execute(
                    "SELECT * FROM jobs WHERE id IN (SELECT job_id FROM assignments WHERE root_id=?) ORDER BY id", (root,))]
                own["campaigns"] = [dict(row) for row in db.execute(
                    "SELECT * FROM evidence_campaigns WHERE job_id IN (SELECT job_id FROM assignments WHERE root_id=?) ORDER BY job_id", (root,))]
                objects = {root} | {row["id"] for table in ("agents", "assignments", "results", "reviews", "jobs") for row in own[table]}
                own["events"] = [dict(row) for row in db.execute("SELECT * FROM events ORDER BY sequence")
                                 if json.loads(row["event_json"])["object_id"] in objects]
                history["history_hash"] = digest(own)
            return {**history, "network_id": self.network_id, "root_id": root, "agent_id": agent,
                    "assigned": grant["assigned"], "max_jobs": grant["max_jobs"],
                    "expires": grant["expires"], "cooldown_until": grant["cooldown_until"],
                    "other_agent_has_lease": bool(active and active["agent_id"] != agent),
                    "lease": self._package(db, active) if active and active["agent_id"] == agent else None}

    def metrics(self):
        """Only aggregates. No identities, artifacts, prompts, signatures, or tokens."""
        with self.store.connect() as db:
            return {"jobs": db.execute("SELECT count(*) FROM jobs").fetchone()[0],
                    "results": db.execute("SELECT count(*) FROM results").fetchone()[0],
                    "promoted": db.execute("SELECT count(*) FROM results WHERE state='promoted'").fetchone()[0]}
