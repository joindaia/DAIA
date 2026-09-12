"""Operator/developer CLI. This is not a required volunteer daemon."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from .crypto import sign, public_hex
from .service import Coordinator
from .store import Store


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
    invite = sub.add_parser("invite")
    invite.add_argument("--max-jobs", type=int, default=20)
    seed = sub.add_parser("seed")
    seed.add_argument("--number", type=int, default=10403)
    sub.add_parser("serve")
    mcp = sub.add_parser("serve-mcp")
    mcp.add_argument("--tailnet-url", help="Exact private Tailscale Serve MCP URL; listener stays loopback")
    revoke = sub.add_parser("revoke")
    revoke.add_argument("root_id")
    args = parser.parse_args()
    if args.command == "demo":
        return demo()
    service = Coordinator(Store(args.db))
    if args.command == "init":
        print("Initialized local development database.")
    elif args.command == "invite":
        print(json.dumps(service.invite(args.max_jobs)))
    elif args.command == "seed":
        print(json.dumps({"job_id": service.seed(args.number)}))
    elif args.command == "revoke":
        service.revoke(args.root_id)
        print("Revoked contributor grant.")
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
