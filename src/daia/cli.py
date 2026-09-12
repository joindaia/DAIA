"""Operator/developer CLI. This is not a required volunteer daemon."""
from __future__ import annotations
import argparse
import json
import os
import sqlite3
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from .crypto import sign, public_hex
from .service import Coordinator, Denied
from .store import Store, backup_database


def verify_evidence_source(document, repository=None):
    """Read raw Git objects only; never apply patches, text converters, or candidate commands."""
    try:
        commit, source = document["baseline_commit"], document["source"]
        path, start, text = source["path"], source["start_line"], source["text"]
        if (not isinstance(commit, str) or len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit)
                or not isinstance(path, str) or not path.startswith(("src/", "tests/", "docs/"))
                or ":" in path or "\\" in path or ".." in path.split("/")
                or type(start) is not int or start < 1 or not isinstance(text, str) or not text):
            raise ValueError()
        def git(*arguments):
            return subprocess.check_output(["git", "--no-replace-objects", "-C", str(repository or Path.cwd()),
                                            *arguments], stderr=subprocess.DEVNULL)
        if git("cat-file", "-t", commit).strip() != b"commit":
            raise ValueError()
        object_name = f"{commit}:{path}"
        if int(git("cat-file", "-s", object_name)) > 1_000_000:
            raise ValueError()
        blob = git("cat-file", "blob", object_name).decode("utf-8")
        lines = blob.splitlines(keepends=True)
        if "".join(lines[start - 1:start - 1 + len(text.splitlines())]) != text:
            raise ValueError()
    except (ValueError, TypeError, KeyError, OSError, subprocess.SubprocessError):
        raise ValueError("Frozen excerpt must exactly match the named local Git commit and lines") from None


def demo():
    with TemporaryDirectory() as temp:
        service = Coordinator(Store(str(Path(temp) / "demo.sqlite3")))
        service.seed()
        result = {}
        for _ in range(3):
            root = service.invite()["root_id"]
            key = Ed25519PrivateKey.generate()
            challenge = service.challenge(root, public_hex(key))
            agent = service.register(root, challenge["challenge_id"], sign(key, challenge))["agent_id"]
            lease = service.request_work(root, agent)
            verdict = "candidate" if lease["mode"] == "produce" else "pass"
            artifact = '{"factors":[101,103]}'
            envelope = service.envelope(root, agent, lease["assignment_id"], artifact, verdict)
            result = service.submit(root, agent, lease["assignment_id"], artifact, verdict, sign(key, envelope))
            print(json.dumps({"mode": lease["mode"], "status": result["status"]}))
        assert result["status"] == "promoted"
        print(json.dumps({"demo": "passed", "metrics": service.metrics()}))


def main():
    parser = argparse.ArgumentParser(description="DAIA local development tools")
    parser.add_argument("--db", default=os.environ.get("DAIA_DB", ".runtime/daia.sqlite3"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo")
    sub.add_parser("init")
    backup = sub.add_parser("backup", help="Operator-only checked private database snapshot")
    backup.add_argument("--output", type=Path, required=True)
    invite = sub.add_parser("invite")
    invite.add_argument("--max-jobs", type=int, default=20)
    seed = sub.add_parser("seed")
    seed.add_argument("--number", type=int, default=10403)
    evidence = sub.add_parser("admit-evidence", help="Operator-only frozen data-only source-analysis campaign")
    evidence.add_argument("--context", type=Path, required=True)
    inspect = sub.add_parser("inspect-evidence", help="Write private campaign evidence for human inspection")
    inspect.add_argument("--output", type=Path, required=True)
    resolve = sub.add_parser("resolve-evidence", help="Human-only evidence disposition; no merge or payout")
    resolve.add_argument("--job", required=True)
    resolve.add_argument("--disposition", choices=["useful", "duplicate", "unclear", "rejected", "cancelled"], required=True)
    resolve.add_argument("--note", required=True)
    sub.add_parser("serve")
    mcp = sub.add_parser("serve-mcp")
    mcp.add_argument("--tailnet-url", help="Exact private Tailscale Serve MCP URL; listener stays loopback")
    revoke = sub.add_parser("revoke")
    revoke.add_argument("root_id")
    args = parser.parse_args()
    if args.command == "demo":
        return demo()
    if args.command == "backup":
        try:
            backup_database(args.db, args.output)
        except (OSError, ValueError, sqlite3.DatabaseError):
            # Publication can precede a cleanup failure; preserve any output for inspection.
            parser.exit(1, "Backup could not be confirmed. Check source integrity and storage permissions. "
                        "Preserve any output. Choose a new filename before retrying.\n")
        print("Private snapshot verified and written. Restoration requires offline maintainer review.")
        return
    if args.command == "inspect-evidence":
        try:
            if args.output.exists() or args.output.is_symlink():
                raise FileExistsError()
            service = Coordinator(Store(args.db, create=False))
            args.output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with TemporaryDirectory(prefix=".daia-inspection-", dir=args.output.parent) as staging:
                temporary = Path(staging) / "inspection.json"
                fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "w", encoding="utf-8") as output:
                    json.dump(service.inspect_evidence(), output, ensure_ascii=False, indent=2)
                    output.flush()
                    os.fsync(output.fileno())
                # Like backups, publish complete bytes exclusively; never replace a raced-in file.
                os.link(temporary, args.output)
        except (OSError, ValueError, TypeError, RecursionError, sqlite3.DatabaseError):
            parser.exit(1, "Inspection export could not be confirmed. Check the database and private storage. "
                        "Preserve any output; inspect it before retrying.\n")
        print("Private evidence inspection written; treat all artifacts as untrusted data.")
        return
    if args.command in {"resolve-evidence", "revoke"}:
        try:
            service = Coordinator(Store(args.db, create=False))
        except (OSError, ValueError, sqlite3.DatabaseError):
            parser.exit(1, "Existing coordinator database could not be opened. Check the database path and private storage.\n")
    else:
        service = Coordinator(Store(args.db))
    if args.command == "init":
        print("Initialized local development database.")
    elif args.command == "invite":
        print(json.dumps(service.invite(args.max_jobs)))
    elif args.command == "seed":
        print(json.dumps({"job_id": service.seed(args.number)}))
    elif args.command == "admit-evidence":
        from .crypto import strict_json
        if args.context.stat().st_size > 16384:
            raise ValueError("Context file exceeds 16 KiB")
        document = strict_json(args.context.read_text(encoding="utf-8-sig"))
        verify_evidence_source(document)
        print(json.dumps(service.admit_evidence(document)))
    elif args.command == "resolve-evidence":
        print(json.dumps(service.resolve_evidence(args.job, args.disposition, args.note)))
    elif args.command == "revoke":
        try:
            service.revoke(args.root_id)
        except Denied:
            parser.exit(1, "Contributor not found. Check its identifier and coordinator database.\n")
        print("Contributor grant is revoked.")
    else:
        import uvicorn
        if args.command == "serve-mcp":
            from .mcp_server import build_mcp_app
            app = build_mcp_app(service, tailnet_url=args.tailnet_url)
        else:
            from .http import create_app
            app = create_app(service)
        # Listener always stays loopback. Optional private Serve routing is operator-owned.
        uvicorn.run(app, host="127.0.0.1", port=8000, access_log=False, log_level="warning")

if __name__ == "__main__":
    main()
