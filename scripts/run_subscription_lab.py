"""Bounded supervisor for the experimental subscription lab, not an installer.

Requires preconfigured Linux service identities, KVM and trusted fixture inputs.
Run as administrator on the dedicated lab host. No new login or quota is granted.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import uuid

parser = argparse.ArgumentParser(description=__doc__)
for name in ("guest", "request-template", "auth-home", "codex-binary", "python-runtime"):
    parser.add_argument("--" + name, type=Path, required=True)
parser.add_argument("--native-delivery", action="store_true")
parser.add_argument("--crash-before-first-response", action="store_true")
args = parser.parse_args()
if os.geteuid() != 0:
    parser.error("Requires the preconfigured lab administrator.")
repo = Path(__file__).resolve().parents[1]
# Shared lab templates require one live controller; stale lock files are harmless.
with open("/run/daia-subscription-lab.lock", "a") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    unit = "daia-controller-job-" + uuid.uuid4().hex + ".service"
    paths = ["/run/daia-lab/" + name for name in (
        "gateway.sock", "model.sock", "subscription-auth.json",
        "rotation-credential.json", "rotation-credential.tmp", "rotation-request",
        "subscription-provider-headers.json", "subscription-provider-error.json",
        "subscription-request.json", "crash-before-first-response", "crash-ready",
    )] + ["/run/daia-research/gateway.sock"]
    if any(Path(p).exists() for p in paths[:2] + paths[-1:]):
        raise SystemExit("Lab endpoint exists; inspect its owner before starting.")
    result = Path("/tmp/daia-live-research-result.json")
    result.unlink(missing_ok=True)  # A previous successful run is never evidence.
    command = [
        "systemd-run", "--quiet", "--wait", "--unit=" + unit,
        "--setenv=DAIA_CONTROLLER_UNIT=" + unit,
        "-p", "Type=exec", "-p", "RuntimeMaxSec=210",
        "-p", "KillMode=control-group", "-p", "TimeoutStopSec=5",
        "-p", "ExecStopPost=/usr/bin/rm -f -- " + " ".join(paths),
        str(args.python_runtime / "bin/python"),
        str(repo / "scripts/run_subscription_lab_controller.py"),
    ]
    for name, value in vars(args).items():
        if name in ("native_delivery", "crash_before_first_response"):
            if value: command += ["--" + name.replace("_", "-")]
            continue
        command += ["--" + name.replace("_", "-"), str(value)]
    try:
        run = subprocess.run(command, capture_output=True, timeout=230)
        clean = not any(Path(p).exists() for p in paths)
        print(json.dumps({"controller_exit": run.returncode,
                          "supervised_endpoints_and_handoffs_removed": clean}), flush=True)
        if run.returncode or not clean:
            raise RuntimeError("Lab failed; inspect bounded private diagnostics.")
        data = json.loads(result.read_text())
        data.update(normal_supervised_controller_exit=0, supervised_cleanup_complete=clean)
        Path("/run/daia-assembled-subscription-result.json").write_text(json.dumps(data))
        print(json.dumps({k: data[k] for k in (
            "results", "overlay_removed", "rotation", "model_channel_counts",
            "normal_supervised_controller_exit", "supervised_cleanup_complete",
        )}))
    finally:
        subprocess.run(["systemctl", "stop", unit], capture_output=True, timeout=20)
        subprocess.run(["systemctl", "reset-failed", unit], capture_output=True, timeout=20)
