"""Export one acknowledged subscription candidate for isolated evaluation.

This reads a retained run and coordinator database only. It never resumes work,
signs, retries, renews consent, or executes the candidate.
"""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3

from daia.crypto import strict_json, digest
from inspect_subscription_run import inspect as inspect_run
from inspect_subscription_run import private, read_json


def _assignment_record(run):
    run = Path(run).absolute()
    result = inspect_run(run)
    if result.get("delivery") != "acknowledged":
        raise ValueError("Completed acknowledged delivery required")

    _, metadata = read_json(run / "run.json")
    assignment_id = metadata.get("assignment_id")
    if not isinstance(assignment_id, str) or not re.fullmatch(r"[0-9a-f]{32}", assignment_id):
        raise ValueError("Exact recorded assignment required")
    states = list((run / "assignment").glob("*.contributor.json"))
    if len(states) != 1:
        raise ValueError("Exactly one saved contributor state required")
    _, saved = read_json(states[0])
    receipt = saved.get("receipt")
    if saved.get("pending") is not None or saved.get("lease") is not None:
        raise ValueError("Completed assignment state required")
    if not isinstance(receipt, dict) or not re.fullmatch(r"[0-9a-f]{64}", receipt.get("receipt_hash", "")):
        raise ValueError("Recorded receipt required")

    database = run / "coordinator/network.sqlite3"
    private(database)
    try:
        with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as db:
            db.execute("PRAGMA query_only=ON")
            db.row_factory = sqlite3.Row
            assignment = db.execute(
                "SELECT id, job_id, agent_id, root_id, nonce, state, receipt_hash "
                "FROM assignments WHERE id=?", (assignment_id,)
            ).fetchone()
            if assignment is None:
                raise ValueError("Recorded assignment missing")
            if assignment["state"] != "submitted" or assignment["receipt_hash"] != receipt["receipt_hash"]:
                raise ValueError("Recorded assignment delivery mismatch")
            rows = db.execute(
                "SELECT id, artifact, artifact_hash, envelope_json, signature "
                "FROM results WHERE job_id=? AND root_id=?",
                (assignment["job_id"], assignment["root_id"]),
            ).fetchall()
            if len(rows) != 1:
                raise ValueError("Exactly one assignment result required")
            return dict(assignment), dict(rows[0])
    except sqlite3.DatabaseError:
        raise ValueError("Coordinator result records unavailable") from None


def export_candidate(run, output):
    output = Path(output)
    if not output.is_absolute():
        raise ValueError("Absolute output path required")
    private(output.parent, directory=True)
    if output.exists() or output.is_symlink():
        raise FileExistsError("Output already exists")

    assignment, result = _assignment_record(run)
    artifact = result.get("artifact")
    if not isinstance(artifact, str) or not artifact or len(artifact.encode("utf-8")) > 4096:
        raise ValueError("Bounded result artifact required")
    artifact_hash = hashlib.sha256(artifact.encode("utf-8")).hexdigest()
    if result.get("artifact_hash") != artifact_hash:
        raise ValueError("Result artifact hash mismatch")

    try:
        envelope = strict_json(result["envelope_json"])
    except (KeyError, TypeError, ValueError, RecursionError):
        raise ValueError("Result envelope unavailable") from None
    signature = result.get("signature")
    if not isinstance(signature, str) or not re.fullmatch(r"[0-9a-f]{128}", signature):
        raise ValueError("Result signature unavailable")
    if not isinstance(envelope, dict):
        raise ValueError("Result envelope unavailable")
    for key, expected in {
        "action": "submit",
        "assignment_id": assignment["id"],
        "job_id": assignment["job_id"],
        "agent_id": assignment["agent_id"],
        "nonce": assignment["nonce"],
        "artifact_hash": artifact_hash,
    }.items():
        if envelope.get(key) != expected:
            raise ValueError("Result envelope assignment binding mismatch")
    if digest({"envelope": envelope, "signature": signature}) != assignment["receipt_hash"]:
        raise ValueError("Result receipt hash mismatch")

    try:
        packet = strict_json(artifact)
    except (TypeError, ValueError, RecursionError):
        raise ValueError("Result artifact JSON unavailable") from None
    suggested = packet.get("suggested_change") if isinstance(packet, dict) else None
    if not isinstance(suggested, str) or not suggested:
        raise ValueError("Result suggested_change missing")
    try:
        if len(suggested.encode("utf-8")) >= 8192:
            raise ValueError("Result suggested_change exceeds bound")
        encoded = json.dumps(suggested, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError("Result suggested_change is not valid UTF-8") from None

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(output, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        output.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        export_candidate(args.run, args.output)
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
