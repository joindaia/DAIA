"""Bounded supervisor for the experimental subscription lab, not an installer.

Requires preconfigured Linux service identities, KVM and trusted fixture inputs.
Run as administrator on the dedicated lab host. No new login or quota is granted.
"""
if not __debug__:
    raise SystemExit("Optimized Python is unsupported for lab execution")

import argparse
import fcntl
import json
import os
import pwd
from pathlib import Path
import subprocess
import uuid
from subscription_lab_outcome import write_outcome
from subscription_lab_identity import check_identities
from subscription_lab_shutdown import verify as verify_revocation

parser = argparse.ArgumentParser(description=__doc__)
for name in ("guest", "request-template", "auth-home", "codex-binary", "python-runtime"):
    parser.add_argument("--" + name, type=Path, required=True)
parser.add_argument("--prepared-host-image", type=Path)
parser.add_argument("--prepared-host-sha256")
parser.add_argument("--native-delivery", action="store_true")
parser.add_argument("--crash-before-first-response", action="store_true")
args = parser.parse_args()
if bool(args.prepared_host_image) != bool(args.prepared_host_sha256):
    parser.error("Prepared image and hash required together.")
# Installation has a separate bounded allowance; the assignment stays at 150s.
controller_seconds = 330 if args.prepared_host_image else 210
if os.geteuid() != 0:
    parser.error("Requires the preconfigured lab administrator.")
check_identities()  # Before lock/state cleanup, service startup or credential access.
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
    for name in ('daia-assembled-subscription-result.json', 'daia-subscription-outcome.json', 'daia-subscription-run.json'):
        Path('/run', name).unlink(missing_ok=True)
    command = [
        "systemd-run", "--quiet", "--wait", "--unit=" + unit,
        "--setenv=DAIA_CONTROLLER_UNIT=" + unit,
        "-p", "Type=exec", "-p", "RuntimeMaxSec=" + str(controller_seconds),
        "-p", "RuntimeDirectory=" + unit.removesuffix(".service"),
        "-p", "RuntimeDirectoryMode=0755",
        "-p", "KillMode=control-group", "-p", "TimeoutStopSec=5",
        "-p", "ExecStopPost=/usr/bin/rm -f -- " + " ".join(paths),
        str(args.python_runtime / "bin/python"),
        str(repo / "scripts/run_subscription_lab_controller.py"),
    ]
    for name, value in vars(args).items():
        if value is None: continue
        if name in ("native_delivery", "crash_before_first_response"):
            if value: command += ["--" + name.replace("_", "-")]
            continue
        command += ["--" + name.replace("_", "-"), str(value)]
    try:
        run = subprocess.run(command, capture_output=True, timeout=controller_seconds + 20)
        clean = not any(Path(p).exists() for p in paths)
        print(json.dumps({"controller_exit": run.returncode,
                          "supervised_endpoints_and_handoffs_removed": clean}), flush=True)
        if run.returncode or not clean:
            raise RuntimeError("Lab failed; inspect bounded private diagnostics.")
        recorded = json.loads(Path('/run/daia-subscription-run.json').read_text())
        revoked = verify_revocation(recorded['state_directory'], controller_unit=unit,
                                    model_uid=pwd.getpwnam('daia-egress').pw_uid)
        data = json.loads(result.read_text())
        data.update(normal_supervised_controller_exit=0, supervised_cleanup_complete=clean,
                    persistent_model_authority_revoked=revoked)
        write_outcome(Path(recorded["state_directory"]) / "integrated-report-private.json", data)
        Path("/run/daia-assembled-subscription-result.json").write_text(json.dumps(data))
        print(json.dumps({k: data[k] for k in (
            "results", "overlay_removed", "rotation", "model_channel_counts",
            "normal_supervised_controller_exit", "supervised_cleanup_complete",
            "persistent_model_authority_revoked",
        )}))
    finally:
        subprocess.run(["systemctl", "stop", unit], capture_output=True, timeout=20)
        subprocess.run(["systemctl", "reset-failed", unit], capture_output=True, timeout=20)
