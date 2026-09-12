"""Linux execution primitive, not a sandbox for an enclosing desktop session.

Only operator-prepared, credential-free input snapshots may be supplied. No host
network, home, helper credentials, or writable host directory is mounted. Research
and helper brokers must be integrated separately before this can host a worker.
"""
import argparse
import os
from pathlib import Path
import stat
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
    # No inherited input descriptor; output remains an untrusted caller stream.
    # bwrap must fail rather than run unconfined.
    try:
        result = subprocess.run(argv, env={'PATH': '/usr/bin:/bin'}, close_fds=True,
                                stdin=subprocess.DEVNULL, start_new_session=True, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        # bwrap's die-with-parent tears down its PID namespace and descendants.
        parser.exit(124, 'Isolated task exceeded its wall-clock limit\n')
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
