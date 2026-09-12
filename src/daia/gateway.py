"""Closed Unix-socket backend; requires a separately secured mutual-TLS proxy."""
import argparse
import os
from pathlib import Path
import socket
import stat
import sqlite3

from .crypto import strict_json
from .mcp_server import build_mcp_app, public_origin
from .service import Coordinator
from .store import Store


def configured_app(config, database):
    with Path(config).open("rb") as source:
        raw = source.read(40001)
    if len(raw) > 40000:
        raise ValueError("Invalid gateway policy")
    policy = strict_json(raw.decode("utf-8"))
    if not isinstance(policy, dict) or set(policy) != {"resource", "allowed_agents", "certificate_agents"}:
        raise ValueError("Invalid gateway policy")
    if not isinstance(policy["resource"], str) or policy["certificate_agents"] is None or policy["allowed_agents"] is None:
        raise ValueError("Closed policy required")
    public_origin(policy["resource"])
    # Existing database only: a misspelled deployment path must not initialize new state.
    return build_mcp_app(Coordinator(Store(str(database), create=False)),
                         allowed_agents=policy["allowed_agents"],
                         certificate_agents=policy["certificate_agents"], public_url=policy["resource"])


def bind_private_socket(path):
    if os.name != "posix":
        raise ValueError("Unix socket required")
    path = Path(path).absolute()
    parent = path.parent
    info = parent.lstat()
    if (parent.resolve() != parent or not stat.S_ISDIR(info.st_mode)
            or info.st_uid != os.geteuid() or info.st_gid != os.getegid()
            or stat.S_IMODE(info.st_mode) != 0o750):
        raise ValueError("Dedicated socket directory must have service ownership and mode 0750")
    for ancestor in parent.parents:
        ancestor_info = ancestor.stat()
        writable = ancestor_info.st_mode & 0o022
        trusted_sticky = ancestor_info.st_uid == 0 and ancestor_info.st_mode & stat.S_ISVTX
        if ancestor_info.st_uid not in {0, os.geteuid()} or (writable and not trusted_sticky):
            raise ValueError("Untrusted socket ancestor")
    # Bind refuses every existing socket, file or symlink. Never unlink another service.
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    previous = os.umask(0o117)
    try:
        listener.bind(str(path))
        info = path.lstat()
        if (not stat.S_ISSOCK(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o660
                or info.st_uid != os.geteuid() or info.st_gid != os.getegid()):
            raise ValueError("Invalid socket permissions")
        listener.listen(128)
        return listener
    except Exception:
        listener.close()
        raise
    finally:
        os.umask(previous)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--socket", type=Path, required=True)
    args = parser.parse_args()
    try:
        app = configured_app(args.config, args.db)
        listener = bind_private_socket(args.socket)
    except (OSError, ValueError, TypeError, RecursionError, sqlite3.DatabaseError):
        parser.exit(1, "Closed gateway refused startup. Check policy, existing database and private socket permissions.\n")
    import uvicorn
    with listener:
        # Prebound socket only. No host/port option or fallback TCP listener exists.
        server = uvicorn.Server(uvicorn.Config(app, proxy_headers=False, access_log=False, log_level="warning"))
        server.run(sockets=[listener])
    # Leave the socket pathname for deliberate operator inspection/removal on restart.


if __name__ == "__main__":
    main()
