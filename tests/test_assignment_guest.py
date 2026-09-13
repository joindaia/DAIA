"""Exercise the guest entrypoint with a local substitute for its fixed VM route."""
import os
import select
import socket
import subprocess
import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Linux guest transport')


@pytest.mark.parametrize('model_closes_first', [True, False])
def test_guest_stdio_preserves_reply_and_eof(model_closes_first):
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        listener.listen(1)
        listener.settimeout(5)
        program = f"""
import socket
from daia.assignment_guest import main
connect = socket.create_connection
def local(address, timeout):
    assert address == ('10.0.2.100', 3128) and timeout == 8
    return connect({listener.getsockname()!r}, timeout=timeout)
socket.create_connection = local
raise SystemExit(main())
"""
        child = subprocess.Popen([sys.executable, '-c', program],
                                 env={**os.environ, 'PYTHONPATH': 'src'},
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        try:
            with listener.accept()[0] as peer:
                peer.settimeout(5)
                child.stdin.write(b'{"id":1}\n'); child.stdin.flush()
                if model_closes_first:
                    child.stdin.close(); child.stdin = None
                data = bytearray()
                while len(data) < len(b'{"id":1}\n'):
                    data.extend(peer.recv(128))
                if model_closes_first:
                    assert peer.recv(1) == b''
                assert bytes(data) == b'{"id":1}\n'
                peer.sendall(b'{"result":"saved"}\n')
                peer.shutdown(socket.SHUT_WR)
            response = bytearray()
            while True:
                assert select.select([child.stdout], [], [], 2)[0], 'helper EOF not forwarded'
                chunk = os.read(child.stdout.fileno(), 128)
                if not chunk:
                    break
                response.extend(chunk)
            if child.stdin is not None:
                child.stdin.close(); child.stdin = None
            out, err = child.communicate(timeout=5)
            assert child.returncode == 0 and not err
            assert not out and bytes(response) == b'{"result":"saved"}\n'
        finally:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=5)
