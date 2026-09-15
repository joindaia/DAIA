# Experimental Linux lab installation basis

These native systemd manifests describe the four service identities and five
storage/socket directories required by the subscription lab. They do not install
Python, KVM/QEMU, images, Codex, credentials, firewall rules or a signed runtime.
They start no services and authorize no participation or provider usage.

Validate on a trusted Linux installation host with:

```sh
sudo python3 scripts/probe_lab_installation.py
```

The probe invokes both systemd tools exclusively with `--root` pointing at a
fresh temporary directory, verifies accounts and directory metadata, repeats the
installation, compares account files, verifies host account files are unchanged,
and removes that temporary root. No actual host installation occurs.

For an eventual reviewed host installation, the sysusers manifest belongs under
`/usr/lib/sysusers.d/` and the tmpfiles manifest under `/usr/lib/tmpfiles.d/`.
Use a trusted administrator/package manager. Do not install from a worker-modifiable
checkout. The current runtime group obtains KVM access through the restricted
service's explicit supplementary group; no login or sudo membership is added.
The `/run` directories must be recreated after reboot by systemd-tmpfiles.

Existing accounts are not repaired or reallocated by sysusers. Run the repository's
`subscription_lab_identity.check_identities` validation before activating the lab;
its refusal is not permission to alter existing users. The startup entrypoints
already invoke that check. Existing unsafe or conflicting installations require
explicit inspection. Tmpfiles can adjust modes/ownership of existing directories:
this probe proves fresh-root behavior, not a safe migration of arbitrary state.

Persistent runs remain private to the trusted controller and no deletion policy
is installed. Retention, backup and disk-capacity management remain outstanding.
The runtime, authenticating client and approved task bundle must still be installed
and verified separately before a complete participant installation can be claimed.

## Fresh-host acceptance boundary

The public preparation script does not provision a host. Before a clean-host
trial, the trusted administrator must supply and validate:

- Linux with systemd as PID 1, usable hardware KVM, QEMU and the ISO builder;
- the four distinct service accounts and protected directories above, including
  recreation of transient socket directories after reboot;
- a verified base at `/var/lib/daia-lab/templates/base.qcow2`;
- the pinned native client and companion binaries, the locked Python runtime,
  and an independently approved request template;
- a separate participant-owned authentication profile, populated only through
  the participant's native provider login.

Do not require a pre-existing `templates/network-seed.iso`: the controller copies
it from the newly prepared guest seed after bundle verification. The base image,
accounts and directory setup are genuine host prerequisites; a prior run's seed
is not. Keep the source checkout, binaries and all trusted-input ancestors outside
worker write access.

For a nested clean-host trial, first verify nested KVM and physical backing-disk
capacity. WSL's virtual filesystem free space alone is insufficient. Preserve the
existing 20 GiB physical-disk reserve and budget additional guest storage before
starting; do not remove retained results or private files to make room implicitly.
A metadata-only second-host preflight on 15 September found KVM and nested KVM
available, systemd active, no running lab units, and physical free space at roughly
that reserve. No additional VM was started. This is capacity/prerequisite evidence,
not a clean-host installation result.

## Separate locked Python runtime

Use Python 3.12 and a trusted `uv` installation from the approved installation
side. Choose a new, absolute runtime destination outside any worker-writable tree.
From the trusted DAIA checkout:

```sh
UV_PROJECT_ENVIRONMENT="$DAIA_RUNTIME_DEST" uv sync --locked --no-editable \
  --extra mcp --python /usr/bin/python3.12
```

The lab controller uses its own small fixture module and actual loopback MCP;
`dev` is no longer required at runtime. Keep the approved checkout available;
this is not yet a standalone controller wheel. `--locked` refuses lock drift and `--no-editable` installs the
DAIA package rather than linking it back to the checkout. The controller still
explicitly uses approved repository source for its lab fixtures.

After the required artifacts have been cached, the same command with `--offline`
can populate another empty destination. Missing artifacts must fail; offline mode
is not a promise that an arbitrary participant already has the cache. This does
not authenticate the installation administrator, repository or build backend.
Protect the final runtime, interpreter, checkout and their ancestors from workers.
Do not copy existing provider profiles into the runtime or install participant
packages in a personal environment.

The 2026-09-13 probe used CPython 3.12.3 and uv 0.12.11. Both newly created
runtimes had the same 39 installed distribution versions. Isolated Python imported
the non-editable DAIA package outside the checkout, and the CLI help worked there.
The full repository suite using the new runtime passed 596 tests, skipped ten
explicit integrations/platform tests, and emitted one dependency deprecation
warning. Pytest still selects repository source; these tests do not prove every
installed-wheel path or a live VM launch with the new runtime. See the
[recorded scope](../../docs/research/clean-locked-runtime-2026-09-13.json).

## Preparing the participant's first native login

Run `prepare_codex_profile.py` as the participant on the trusted installation
side, with the approved original client and a new profile beneath an existing
private participant-owned parent directory:

```sh
python3 scripts/prepare_codex_profile.py --binary "$DAIA_CODEX_BINARY" \
  --home "$DAIA_AUTH_HOME"
```

The tool checks the pinned binary digest, creates a new 0700 profile and 0600
configuration selecting file storage and ChatGPT login, and stops. Existing
profiles are refused. It does not run Codex, copy credentials or register work.
Protect the binary, profile ancestors and scripts against modification by workers.
This check is not protection from the trusted owner changing them afterward.

The participant can then start the original client's login in their own trusted
terminal, with no imported environment or personal Codex configuration:

```sh
env -i PATH=/usr/bin:/bin HOME="$DAIA_AUTH_HOME" CODEX_HOME="$DAIA_AUTH_HOME" \
  "$DAIA_CODEX_BINARY" login --device-auth
```

This command is a separate interactive action, not run by preparation. The
participant completes the provider page themselves. Do not capture its code or
tokens in project logs or pass the profile to the worker VM. Use the existing
outside-worker authentication path after login and private-file validation.

The [official authentication documentation](https://learn.chatgpt.com/docs/auth)
describes device-code login, `CODEX_HOME` file storage and cached token renewal.
A clean native login is not proof of inference-only account authority; the external
model boundary is still required. Five preparation tests passed, including an
optimized-Python invalid-binary rejection. The actual pinned client's login help
was checked in a temporary prepared profile: device-auth was available and no
authentication file was created. A new provider login was not performed.


## Python execution mode

The lab entrypoints require normal Python execution: do not set `PYTHONOPTIMIZE`
or pass `-O`/`-OO`. They stop before imports or side effects in those modes because
some lab invariant checks still use assertions. This is separate from the native
authentication probe, whose security checks are explicit and remain enforced with
optimization. Do not remove the entrypoint guard to bypass a refused launch.

## Exact Ubuntu base image

The tested base is `noble-server-cloudimg-amd64.img` from the dated
[Ubuntu 20260911 directory](https://cloud-images.ubuntu.com/noble/20260911/).
Obtain that image, `SHA256SUMS` and `SHA256SUMS.gpg` from the same directory on the
trusted installation side. Do not substitute the mutable `current` directory.
The installation host must have Ubuntu's trusted cloudimage keyring at
`/usr/share/keyrings/ubuntu-cloudimage-keyring.gpg` and `gpgv` available; a keyring
supplied with untrusted task input is not an acceptable replacement.

```sh
python3 scripts/verify_lab_base_image.py --image "$DAIA_BASE_IMAGE" \
  --checksums "$DAIA_IMAGE_SUMS" --signature "$DAIA_IMAGE_SIGNATURE"
```

The offline verifier checks immutable temporary copies of the checksum/signature
inputs, requires the single approved image entry, and streams the image hash.
It requires SHA-256
`612b2c0cc1bc413a6cb8c38fd611794caf0f2b436c50013d8b3794db12ad7354`
and exactly 625256960 bytes. It neither mounts nor boots nor installs the image.
A trusted installer must copy the verified bytes into protected template storage;
`prepare_kvm_bundle.py` separately rechecks copied bytes before launch.

The live verification used freshly downloaded dated signature/checksum metadata
against the existing image and passed. Tampered metadata and a wrong image were
rejected. Seven verifier/bundle regressions passed. This identifies the current
lab image; it does not establish an up-to-date vulnerability baseline, a future
image's compatibility, or a complete fresh-host deployment. Image updates require
reviewed new pins and a new acceptance run, never automatic fallback.


## Rebuilding the approved development input

The public development fixture can be rebuilt from this checkout before the
native MCP delivery variant is produced. Use new output directories and the
existing, separately reviewed request template; do not harvest personal prompts
or credentials to create a template. The original Codex and bwrap binaries must
be in the trusted native directory. The first builder checks their pinned hashes.
The ISO builder is a trusted installation dependency, not supplied by task data.

```sh
python3 scripts/prepare_subscription_fixture.py \
  --template "$DAIA_APPROVED_REQUEST_TEMPLATE" --native "$DAIA_NATIVE_DIRECTORY" \
  --output "$DAIA_SOURCE_FIXTURE" --iso-builder "$DAIA_ISO_BUILDER" \
  --base-sha256 612b2c0cc1bc413a6cb8c38fd611794caf0f2b436c50013d8b3794db12ad7354
python3 scripts/prepare_native_delivery_fixture.py \
  --source "$DAIA_SOURCE_FIXTURE" --output "$DAIA_NATIVE_FIXTURE" \
  --native-directory "$DAIA_NATIVE_DIRECTORY" --iso-builder "$DAIA_ISO_BUILDER"
```

Protect these inputs, outputs and ancestors from workers throughout both steps.
The native variant transforms the approved source fixture; it is not a validator
for arbitrary cloud-init input. Neither builder logs in or calls the provider.
Pass the final directory as `--guest` to the bounded lab supervisor. New nonces
and generated ISO metadata mean this is functional reproducibility, not identical
image bytes on repeated builds. Do not publish generated request templates or ISOs.

A fresh two-stage build was used in the real subscription run recorded in
[fresh fixture chain evidence](../../docs/research/fresh-fixture-chain-2026-09-13.json).
This still reuses the trusted native binaries, ISO utility, base image, host
services, approved template and participant login. Their acquisition and the
complete fresh-host installation remain separate release requirements.


## Installed runtime vulnerability audit

Run the audit tool separately from the worker runtime, without `--fix`:

```sh
uv tool run --from pip-audit==2.10.1 pip-audit \
  --path "$DAIA_RUNTIME_DEST/lib/python3.12/site-packages" \
  --format json --desc off --output "$DAIA_AUDIT_REPORT" --progress-spinner off
```

Inspect JSON skips as well as the exit status. The tested 31-package runtime
contained 30 external packages with no published vulnerabilities reported by
PyPI on 2026-09-13. Only the local `daia-coordinator` package was skipped because
it is not available from PyPI. The full audit name set matched installed metadata,
and all installed name/version pairs matched `uv.lock`. Runtime packages were not
modified. [Full scoped evidence](../../docs/research/subscription-runtime-advisory-audit-2026-09-13.json)
includes the exact lock digest and versions.

This is a dated advisory lookup, not a source review or assurance against unknown
vulnerabilities. Repeat before release. Host/guest OS packages, native binaries,
optional extras and the website need separate checks. Tool behavior and limits
are documented by [PyPA pip-audit](https://github.com/pypa/pip-audit).


## One-command clean preparation

The trusted installer can now prepare a new checkout, locked non-editable runtime
and native-delivery guest together. Supply a reviewed full 40-character commit,
trusted tools, signed image metadata, approved native binaries and request template:

```sh
python3 scripts/prepare_clean_subscription_lab.py \
  --repository https://github.com/joindaia/DAIA.git --revision "$DAIA_COMMIT" \
  --output "$DAIA_NEW_PREPARATION" --cache "$DAIA_BUILD_CACHE" \
  --uv "$DAIA_UV" --python /usr/bin/python3.12 \
  --image "$DAIA_BASE_IMAGE" --checksums "$DAIA_IMAGE_SUMS" \
  --signature "$DAIA_IMAGE_SIGNATURE" --template "$DAIA_APPROVED_REQUEST_TEMPLATE" \
  --native "$DAIA_NATIVE_DIRECTORY" --iso-builder "$DAIA_ISO_BUILDER"
```

Output must be a new absolute directory under protected installer-owned ancestors.
It contains `source`, `runtime`, `source-fixture`, `guest` and `prepared.json`.
The build uses a new HOME and a small explicit environment. It does not import
personal Git configuration or credentials. Public repository access is required;
no authentication prompt is enabled. A local trusted Git repository also works.
Only the exact commit is checked out; uncommitted personal files are not copied.
A failed build leaves its private partial destination for inspection; use another
new destination after resolving the failure. Nothing is automatically deleted.

`--offline` applies to Python dependency installation only; Git fetching remains
a separate operation. A new empty cache needs downloads. The base verifier checks
Ubuntu's system-trusted signature and image pin before installation. Native binary
pins are checked by the existing fixture builder. The installer, build backend,
Git, uv, interpreter and ISO utility remain trusted, not sandboxed task code.
The output contains the approved request template and must remain private.

This is preparation, not a full host installer: no service accounts, firewall,
KVM configuration, participant login, model calls or VM launches occur. It still
requires separately acquired native tools, base image and approved request input.
Use `guest` and `runtime` with the existing lab supervisor after host setup.
The actual online fresh-checkout/empty-cache build is recorded in
[clean preparation evidence](../../docs/research/clean-subscription-preparation-2026-09-13.json).

## Second development task: operator outcome summary

The outcome-summary task uses an exact committed copy of the existing lab outcome
module. Its requested addition counts completed work separately from acknowledged,
stored-but-unacknowledged and unconfirmed delivery. It is a small practical feature,
not proof of arbitrary multi-file repository work.

After building the native-delivery fixture above:

```sh
python3 scripts/prepare_outcome_summary_fixture.py \
  --source "$DAIA_NATIVE_FIXTURE" --output "$DAIA_SUMMARY_FIXTURE" \
  --native "$DAIA_NATIVE_DIRECTORY" --iso-builder "$DAIA_ISO_BUILDER"
```

The builder writes the frozen task document and binds its digest in `config.json`.
The controller checks this binding before service startup and admits that exact
source context. These remain trusted installer inputs; a worker cannot choose its
own task or change the coordinator's source-path policy. A legacy version task
without a task document remains supported.

The evidence protocol limits each result text field to 1,200 characters. Therefore
this task returns only the appended function, not the complete original module.
The evaluator combines those unchanged bytes with the fixed original module inside
a new networkless VM. Select `--task outcome-summary` when invoking
`prepare_version_evaluator.py`. It requires one appended `summarize_outcomes`
function and checks seven cases, generator inputs, unchanged inputs and integer
counts. Candidate code runs under the existing unprivileged evaluator identity;
the trusted parent compares output. Nothing is automatically merged or released.

The real second-task trial produced one stored function addition. It exhausted its
six-request allowance before the native receipt retry; the existing operator
recovery command recovered the exact receipt with no model calls or consent change.
A separate networkless evaluator passed seven cases. The maintainer reviewed and
integrated those exact function bytes and connected them to retained-run inspection:

```sh
python3 scripts/inspect_subscription_run.py --run "$DAIA_RUN_ONE" --run "$DAIA_RUN_TWO"
```

One `--run` retains the prior detailed result. Multiple `--run` arguments return
only delivery counts; worker completion is explicitly not established by receipt
inspection. The real two-run check returned one acknowledged and one unconfirmed
run. No accounts, receipts or paths are included in that summary.
[Full evidence and failed attempts](../../docs/research/outcome-summary-subscription-task-2026-09-13.json)
record 33 targeted regression checks. The client turn itself did not complete;
this is a recovered useful contribution, not a passing unattended-turn release gate.

### Helper-side receipt retry

The outcome-summary preparation now explicitly enables `retry_receipt` in its
trusted configuration. The assignment-only helper can then retry one failed
submission with the same saved artifact, verdict, assignment and signature. It
uses the existing submission validation and idempotent receipt path; it does not
request work, renew consent, replenish model requests or sign a replacement result.
A second failure remains pending. Cancellation is not intercepted.

This option is disabled by default for other assignment helpers and is not a
model-facing tool argument. The worker calls `submit_result` once. The simulated
first response loss still occurs outside the worker; the helper, rather than a
second model turn, obtains the receipt. A complete worker turn is still a separate
requirement from successful delivery.


## Continuing a bounded second-host trial

Use the existing prepared host and reviewed entrypoints. Remote access is a
separate prerequisite: a listed SSH public key does not prove the agent can sign,
and a successful connection does not establish a safe worker. Do not weaken host
key checking or start an unbounded fallback when access fails.

Before another provider-backed attempt:

1. Confirm KVM, the separate lab/provider identities, the protected native client
   and the physical backing volume's agreed free-space reserve. On WSL, virtual
   filesystem capacity alone does not establish free Windows disk space. Inspect
   active lab services and retained runs before modifying shared templates.
2. Pin a reviewed full source commit and verify that its `uv.lock` matches the
   installed runtime. Verify the prepared seed/base hashes and the approved
   request's model against the guest configuration. Rebuild with the existing
   preparation commands when these differ; do not silently substitute a model.
3. Inspect the previous private run with the existing read-only command:

   ```sh
   python3 scripts/inspect_subscription_run.py --run "$DAIA_PREVIOUS_RUN"
   ```

   Inspection establishes delivery status, not remaining model allowance or
   permission to resume. A revoked ledger stays revoked. Preserve the old state,
   identity, pending artifact and receipts; use the separately documented exact
   receipt-recovery route only when applicable, without model use or new work.
4. Establish that the participant has authorized this new bounded attempt. The
   lab controller creates a new local fixture network and contributor; it does
   not import an existing participant's remaining consent. Its five-minute helper
   consent, six-request model ledger and at-most-150-second model deadline bound
   that attempt, but do not themselves supply participant authorization. Repeated
   launcher calls are new attempts, not recovery of a previous allowance.
5. Once those conditions hold, use the supervised command in
   [the launcher guide](../../docs/kvm-launcher.md#repository-native-subscription-lab-controller)
   with `--native-delivery` and the matching approved fixture. Record the exact
   source, runtime lock and task inputs privately. Do not call the child controller
   directly or treat a successful preparation as a completed task.

After service termination, use the retained run rather than relying only on
`/run`, which disappears after reboot. Keep raw worker diagnostics private and
untrusted. A zero remaining-request count after revocation is not a usage count;
missing counters mean unavailable. The supervisor separately checks matching
persistent revocation before reporting success. A receipt establishes delivery;
require a completed native turn and a separate networkless evaluation of the
stored source bytes before calling the development trial successful.

The previous failed trial and diagnostic-retention change are described in
[second-host evidence](../../docs/research/second-host-failure-retention-2026-09-13.md).
These instructions add no login, consent renewal, scheduling, automatic recovery
or release authority.

## Fresh RAM-host provisioning experiment (15 September 2026)

A fresh networkless KVM guest, using the pinned Ubuntu base and a 512 MiB
RAM-backed writable overlay, installed the public sysusers/tmpfiles manifests.
Its trusted probe first checked the four accounts were absent, then verified four
distinct nonroot nologin accounts, five directory modes and repeat installation
without passwd changes. Nested `/dev/kvm` returned API version 12. The outer
service stopped and its RAM overlay was removed. No provider was used.

The initial empty network configuration delayed cloud-init until roughly 137 s
and exceeded the 150 s limit. Using the existing evaluator's optional, DHCP-free
network configuration allowed normal guest poweroff around 45 s. The host report
parser still rejected the result: cloud-init prefixed its valid report with a
timestamp and process label. A diagnostic run captured the successful report at
14.22 s. Offline replay accepted that exact prefixed report and a bare report, and
rejected duplicates, a wrong nonce and an unexpected prefix (five checks). No VM
was rerun after the parser correction; the whole harness must still complete
normally before it is advertised as a working installation test.

This is provisioning evidence from a trusted test payload, not hostile-guest
attestation. It reuses the host QEMU and pinned base and does not install QEMU,
Python dependencies or provider authentication in the fresh guest. Nor does KVM
API availability alone prove a nested worker has booted. Those remain subsequent
clean-installation steps. The experimental harness is not yet a public installer.

The corrected precursor harness subsequently completed with return code zero,
all five provisioning fields present, service stopped and RAM overlay removed.
The repository now contains `scripts/probe_fresh_host_ram.py` and its trusted
guest fixture, plus five parser replay regressions. The packaged script reads
the repository manifests, bounds failure-log reads and exits nonzero on probe
failure. Those packaging changes passed the replay tests; the public entrypoint
has not yet been rerun live. Use normal Python as the trusted lab administrator.
This remains a prerequisite probe, not installation of the full subscription worker.
