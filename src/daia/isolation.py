"""Linux execution primitive, not a sandbox for an enclosing desktop session.

Only operator-prepared, credential-free input snapshots may be supplied. No host
network, home, helper credentials, or writable host directory is mounted. Research
and helper brokers must be integrated separately before this can host a worker.
"""
import argparse
import os
from pathlib import Path
import stat
import selectors
import time
import subprocess
import sys


EXCLUDED = {'.git', '.private', '.runtime', '.codex', '.env', '.ssh'}


def sandbox_command(snapshot, command):
    source = Path(snapshot).absolute()
    if (sys.platform != 'linux' or not Path('/usr/bin/bwrap').is_file()
            or not source.is_dir() or source.resolve() != source
            or source == Path('/') or not command):
        raise ValueError('Linux bubblewrap and an explicit input snapshot are required')
    # The operator must keep this snapshot immutable during execution. This check
    # rejects common accidental checkout mounts; it is not a secret detector.
    for path in [source, *source.rglob('*')]:
        info = path.lstat()
        mode = info.st_mode
        if (path.name in EXCLUDED or path.name.startswith('.env.')
                or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode))
                or (stat.S_ISREG(mode) and info.st_nlink != 1)):
            raise ValueError('Input must be a clean snapshot of regular files')
    return [
        '/usr/bin/bwrap', '--unshare-all', '--unshare-user', '--disable-userns',
        '--assert-userns-disabled', '--die-with-parent', '--new-session',
        '--cap-drop', 'ALL', '--clearenv',
        '--ro-bind', '/usr', '/usr',
        '--symlink', 'usr/bin', '/bin', '--symlink', 'usr/lib', '/lib',
        '--symlink', 'usr/lib64', '/lib64',
        '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp',
        '--tmpfs', '/work', '--dir', '/home', '--dir', '/home/worker',
        '--ro-bind', str(source), '/input', '--chdir', '/work',
        '--setenv', 'HOME', '/home/worker',
        '--setenv', 'PATH', '/usr/bin:/bin',
        '--setenv', 'LANG', 'C.UTF-8', '--', *command,
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--timeout', type=int, default=300, help='Wall-clock limit, 1-3600 seconds')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 3600:
        parser.error('Timeout must be between 1 and 3600 seconds')
    command = args.command
    if command[:1] == ['--']:
        command = command[1:]
    try:
        argv = sandbox_command(args.input, command)
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')
    # Bound combined output before forwarding it. The caller must still treat
    # those bytes as untrusted; this CLI is not a desktop-session boundary.
    process = subprocess.Popen(argv, env={'PATH': '/usr/bin:/bin'}, close_fds=True,
                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
    deadline = time.monotonic() + args.timeout
    remaining_output = 1024 * 1024
    captured_out, captured_err = bytearray(), bytearray()
    try:
        with selectors.DefaultSelector() as streams:
            streams.register(process.stdout, selectors.EVENT_READ, captured_out)
            streams.register(process.stderr, selectors.EVENT_READ, captured_err)
            while streams.get_map():
                remaining_time = deadline - time.monotonic()
                if remaining_time <= 0:
                    parser.exit(124, 'Isolated task exceeded its wall-clock limit\n')
                for key, _ in streams.select(min(remaining_time, 0.1)):
                    chunk = os.read(key.fileobj.fileno(), 8192)
                    if not chunk:
                        streams.unregister(key.fileobj)
                        continue
                    if len(chunk) > remaining_output:
                        parser.exit(125, 'Isolated task exceeded its output limit\n')
                    remaining_output -= len(chunk)
                    key.data.extend(chunk)
        try:
            code = process.wait(timeout=max(0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            parser.exit(124, 'Isolated task exceeded its wall-clock limit\n')
    finally:
        if process.poll() is None:
            process.kill()  # Destroy the bwrap PID namespace, including descendants.
        process.wait()
        process.stdout.close()
        process.stderr.close()
    sys.stdout.buffer.write(captured_out)
    sys.stderr.buffer.write(captured_err)
    raise SystemExit(code)


if __name__ == '__main__':
    main()
