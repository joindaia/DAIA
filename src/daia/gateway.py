"""Closed Unix-socket backend; requires a separately secured mutual-TLS proxy."""
import argparse
import os
from pathlib import Path
import socket
import stat
import sqlite3
import signal

from .crypto import strict_json
from .mcp_server import build_mcp_app, public_origin
from .service import Coordinator
from .store import Store


def configured_app(config, database):
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    with os.fdopen(os.open(config, flags), "rb") as source:
        info = os.fstat(source.fileno())
        if (not stat.S_ISREG(info.st_mode) or Path(config).is_symlink()
                or (os.name == "posix" and
                    (info.st_uid not in {0, os.geteuid()} or info.st_mode & 0o022))):
            raise ValueError("Policy must be a trusted, non-writable regular file")
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
    created = None
    try:
        listener.bind(str(path))
        info = path.lstat()
        created = (info.st_dev, info.st_ino)
        if (not stat.S_ISSOCK(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o660
                or info.st_uid != os.geteuid() or info.st_gid != os.getegid()):
            raise ValueError("Invalid socket permissions")
        listener.listen(128)
        return listener
    except Exception:
        listener.close()
        if created is not None:
            remove_own_socket(path, created)
        raise
    finally:
        os.umask(previous)


def remove_own_socket(path, identity):
    try:
        current = Path(path).lstat()
        if stat.S_ISSOCK(current.st_mode) and (current.st_dev, current.st_ino) == identity:
            Path(path).unlink()
    except FileNotFoundError:
        pass


def run_bound(app, listener, path):
    import uvicorn
    info = Path(path).lstat()
    identity = (info.st_dev, info.st_ino)
    try:
        with listener:
            server = uvicorn.Server(uvicorn.Config(app, proxy_headers=False, access_log=False, log_level="warning"))
            # Uvicorn replays SIGTERM after graceful shutdown. Keep that replay
            # graceful too, so our owned socket is removed before process exit.
            previous = signal.signal(signal.SIGTERM, server.handle_exit)
            try:
                server.run(sockets=[listener])
            finally:
                signal.signal(signal.SIGTERM, previous)
            if not server.started:
                raise ValueError("ASGI startup failed")
    finally:
        remove_own_socket(path, identity)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--socket", type=Path, required=True)
    args = parser.parse_args()
    try:
        app = configured_app(args.config, args.db)
        listener = bind_private_socket(args.socket)
        run_bound(app, listener, args.socket)
    except (OSError, ValueError, TypeError, RecursionError, sqlite3.DatabaseError):
        parser.exit(1, "Closed gateway refused startup. Check policy, existing database and private socket permissions.\n")


if __name__ == "__main__":
    main()
