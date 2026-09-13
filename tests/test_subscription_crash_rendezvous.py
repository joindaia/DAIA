"""Exercise the actual lab forward callback without loading credentials/services."""
import ast
from pathlib import Path
import threading
import time
import types
import pytest
from daia.model_request import Denied


def callback(tmp_path, clock):
    source = Path(__file__).parents[1] / 'scripts/probe_subscription_channel_server.py'
    definition = next(n for n in ast.parse(source.read_text()).body
                      if isinstance(n, ast.FunctionDef) and n.name == 'forward')
    class Binding:
        revoked = False
        calls = 0
        def __call__(self, raw):
            self.calls += 1
            return b'synthetic response'
        def revoke(self):
            self.revoked = True
    binding = Binding()
    state = {'root': tmp_path, 'time': clock, 'binding': binding,
             'counts': {'attempts': 0, 'forwarded': 0}, 'Denied': Denied}
    exec(compile(ast.Module(body=[definition], type_ignores=[]), str(source), 'exec'), state)
    return state


def test_first_response_waits_for_trusted_crash_ack(tmp_path):
    state = callback(tmp_path, time)
    marker = tmp_path / 'crash-before-first-response'; marker.touch()
    output = []
    thread = threading.Thread(target=lambda: output.append(state['forward'](b'{}')))
    thread.start()
    try:
        end = time.monotonic() + 2
        while not (tmp_path / 'crash-ready').exists():
            assert time.monotonic() < end
            time.sleep(.01)
        assert output == [] and state['counts']['forwarded'] == 1
        assert state['binding'].calls == 1
    finally:
        marker.unlink(missing_ok=True)
        thread.join(2)
    assert not thread.is_alive() and output == [b'synthetic response']
    assert not state['binding'].revoked


def test_missing_controller_ack_revokes_binding(tmp_path):
    ticks = iter(range(100))
    state = callback(tmp_path, types.SimpleNamespace(monotonic=lambda: next(ticks), sleep=lambda _: None))
    (tmp_path / 'crash-before-first-response').touch()
    with pytest.raises(Denied, match='did not acknowledge'):
        state['forward'](b'{}')
    assert state['binding'].revoked and state['binding'].calls == 1
