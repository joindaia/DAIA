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
