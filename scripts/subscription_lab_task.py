"""Trusted prepared task data; never imports or executes contributed source."""
import hashlib
import json
from pathlib import Path


def load_task(source, config):
    path = Path(source) / 'task.json'
    if 'task_sha256' not in config:
        if path.exists():
            raise ValueError('Unbound task document')
        return {'objective': 'Find the numeric-version comparison bug in this frozen public fixture.',
                'baseline_commit': 'a' * 40,
                'source': {'path': 'src/version_check.py', 'start_line': 1,
                           'text': 'def newer(a, b): return a > b\n'}}
    with path.open('rb') as stream:
        raw = stream.read(16385)
    if len(raw) > 16384 or hashlib.sha256(raw).hexdigest() != config['task_sha256']:
        raise ValueError('Prepared task digest mismatch')
    task = json.loads(raw)
    if not isinstance(task, dict) or set(task) != {'objective','baseline_commit','source'}:
        raise ValueError('Expected frozen task document')
    # Coordinator.admit_evidence applies the full source/schema constraints.
    return task


def load_model_template(path, pinned):
    """Require the gateway and prepared guest to use the same operator choice."""
    with Path(path).open('rb') as stream:
        raw = stream.read(256 * 1024 + 1)
    if len(raw) > 256 * 1024:
        raise ValueError('Request template too large')
    request = json.loads(raw)
    # Older prepared guests contain the literal Spark model.
    if (not isinstance(request, dict) or not isinstance(request.get('model'), str)
            or not request['model'] or request['model'] != pinned.get('model', 'gpt-5.3-codex-spark')):
        raise ValueError('Prepared guest and approved request model differ')
    return request
