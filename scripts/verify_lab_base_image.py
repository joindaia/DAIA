"""Offline verification of the exact Ubuntu base used by the KVM lab.

No installation, download, mount, guest execution or credential access. The trusted
installation supplies Ubuntu's system cloudimage keyring and protects the inputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

IMAGE = 'noble-server-cloudimg-amd64.img'
PIN = '612b2c0cc1bc413a6cb8c38fd611794caf0f2b436c50013d8b3794db12ad7354'
SIZE = 625256960
SOURCE = 'https://cloud-images.ubuntu.com/noble/20260911/'
KEYRING = '/usr/share/keyrings/ubuntu-cloudimage-keyring.gpg'


def bounded(path, limit):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Regular verification input required')
    with path.open('rb') as stream: raw = stream.read(limit + 1)
    if len(raw) > limit: raise ValueError('Verification input too large')
    return raw


def verify(image, checksums, signature):
    manifest = bounded(checksums, 128*1024)
    sig = bounded(signature, 4096)
    # Verify snapshots, so parsing uses the exact bytes passed to gpgv.
    with tempfile.TemporaryDirectory(prefix='daia-image-signature-') as folder:
        root = Path(folder)
        (root/'SHA256SUMS').write_bytes(manifest)
        (root/'SHA256SUMS.gpg').write_bytes(sig)
        result = subprocess.run(['gpgv','--keyring',KEYRING,
            str(root/'SHA256SUMS.gpg'),str(root/'SHA256SUMS')],
            capture_output=True,timeout=15)
        if result.returncode: raise ValueError('Ubuntu checksum signature rejected')
    entries = [line.split() for line in manifest.decode('ascii').splitlines()]
    matches = [p[0] for p in entries if len(p)==2 and p[1].lstrip('*')==IMAGE]
    if matches != [PIN]: raise ValueError('Exact approved image checksum required')
    image = Path(image)
    if image.is_symlink() or not image.is_file(): raise ValueError('Regular base image required')
    with image.open('rb') as stream:
        stream.seek(0,2)
        if stream.tell()!=SIZE: raise ValueError('Base image size mismatch')
        stream.seek(0)
        if hashlib.file_digest(stream,'sha256').hexdigest()!=PIN:
            raise ValueError('Base image digest mismatch')
    return {'image':IMAGE,'source':SOURCE,'sha256':PIN,'bytes':SIZE,
            'signature_verified':True,'booted':False,'installed':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('image','checksums','signature'): p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args()
    print(json.dumps(verify(a.image,a.checksums,a.signature)))
