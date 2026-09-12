"""Operator-only: issue a bounded pilot invite to a private file, never stdout."""
import argparse
import json
import os
from pathlib import Path

from daia.mcp_server import pilot_origin
from daia.service import Coordinator
from daia.store import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--url", required=True)
    parser.add_argument("--max-jobs", type=int, default=3)
    args = parser.parse_args()
    pilot_origin(args.url)
    args.output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    service = Coordinator(Store(args.db))
    grant = None
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            grant = service.invite(max_jobs=args.max_jobs)
            json.dump({**grant, "network_id": service.network_id, "url": args.url}, output)
    except Exception:
        if grant:
            service.revoke(grant["root_id"])
        raise
    print("Private invite written. Expires in 24 hours. Do not paste its contents into a prompt.")


if __name__ == "__main__":
    main()
