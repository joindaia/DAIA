"""Operator-only: issue a bounded pilot invite to a private file, never stdout."""
import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

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
    grant = None
    try:
        pilot_origin(args.url)
        if args.output.exists() or args.output.is_symlink():
            raise FileExistsError()
        service = Coordinator(Store(args.db))
        args.output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with TemporaryDirectory(prefix=".daia-invite-", dir=args.output.parent) as staging:
            temporary = Path(staging) / "invite.json"
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as output:
                grant = service.invite(max_jobs=args.max_jobs)
                json.dump({**grant, "network_id": service.network_id, "url": args.url}, output)
                output.flush()
                os.fsync(output.fileno())
            os.link(temporary, args.output)
    except Exception:
        outcome = "Revocation could not be confirmed. Check the coordinator privately."
        if grant:
            try:
                service.revoke(grant["root_id"])
                outcome = "The newly issued grant was revoked."
            except Exception:
                pass
        parser.exit(1, "Invite creation could not be confirmed. " + outcome
                    + " Do not use or share any output from this attempt. Preserve existing files.\n")
    print("Private invite written. Expires in 24 hours. Do not paste its contents into a prompt.")


if __name__ == "__main__":
    main()
