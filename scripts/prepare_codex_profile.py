"""Prepare an empty private native-login profile on the trusted Linux side.

Never starts Codex, reads another profile, copies credentials or authorizes jobs.
The participant performs the separate native login in their own trusted terminal.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat

PIN = '56ef98ab4032d317ab26e9b5e5a175650717351edb16ed9cde0cb6d1734d62da'


def prepare(binary, home):
    binary, home = Path(binary), Path(home)
    if not binary.is_absolute() or binary.is_symlink() or not binary.is_file():
        raise ValueError('Pinned regular client required')
    with binary.open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest() != PIN:
            raise ValueError('Native client digest mismatch')
    parent = home.parent
    if not home.is_absolute() or '..' in home.parts or parent.is_symlink():
        raise ValueError('Private absolute profile location required')
    info = parent.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('Private participant-owned parent required')
    home.mkdir(mode=0o700)  # Exclusive: never reuse or modify an existing profile.
    config = 'cli_auth_credentials_store = "file"\nforced_login_method = "chatgpt"\n'
    fd = os.open(home/'config.toml', os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600)
    with os.fdopen(fd,'w') as stream:
        stream.write(config); stream.flush(); os.fsync(stream.fileno())
    return {'profile_prepared':True,'login_started':False,'credentials_copied':False}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary',required=True,type=Path)
    parser.add_argument('--home',required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(prepare(args.binary,args.home)))
