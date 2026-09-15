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

For a **new dedicated Ubuntu 24.04 amd64 host**, these are the administrator
commands. First inspect any existing DAIA users/directories; these commands are
not a migration or repair procedure. Run from the reviewed, protected checkout:

```sh
set -eu
sudo apt-get update
sudo apt-get install --no-install-recommends qemu-system-x86 qemu-utils \
  genisoimage python3-venv python3-pip ubuntu-cloudimage-keyring gpgv bubblewrap
sudo install -m 0644 deploy/subscription-lab/daia-lab.sysusers.conf \
  /usr/lib/sysusers.d/daia-lab.conf
sudo install -m 0644 deploy/subscription-lab/daia-lab.tmpfiles.conf \
  /usr/lib/tmpfiles.d/daia-lab.conf
sudo systemd-sysusers /usr/lib/sysusers.d/daia-lab.conf
sudo systemd-tmpfiles --create /usr/lib/tmpfiles.d/daia-lab.conf
test -c /dev/kvm
```

The selected Ubuntu package repositories must already be trusted by the host.
The setup above grants no user sudo/login access and starts no DAIA jobs.

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

## Path choices for the commands below

Use a dedicated trusted installer shell, a protected reviewed checkout and new
absolute output directories. For example, with write access to `/srv/daia`:

```sh
set -eu
DAIA_NATIVE_DIRECTORY=/srv/daia/inputs/native
DAIA_CODEX_BINARY="$DAIA_NATIVE_DIRECTORY/codex"
DAIA_BASE_IMAGE=/srv/daia/inputs/noble-server-cloudimg-amd64.img
DAIA_IMAGE_SUMS=/srv/daia/inputs/SHA256SUMS
DAIA_IMAGE_SIGNATURE=/srv/daia/inputs/SHA256SUMS.gpg
DAIA_RUNTIME_DEST=/srv/daia/reviewed/runtime
DAIA_SOURCE_FIXTURE=/srv/daia/source-fixture
DAIA_NATIVE_FIXTURE=/srv/daia/native-fixture
DAIA_PREBOOT_FIXTURE=/srv/daia/preboot-fixture
DAIA_ISO_BUILDER=/usr/bin/genisoimage
DAIA_PACKAGE_PLAN=/srv/daia/package-plan
DAIA_PACKAGE_CACHE=/srv/daia/package-cache
DAIA_PYTHON_WORK=/srv/daia/python-build
DAIA_PREPARED_IMAGE=/srv/daia/prepared-image/host.qcow2
DAIA_NEW_PREPARATION=/srv/daia/reviewed
DAIA_BUILD_CACHE=/srv/daia/build-cache
```

Choose `DAIA_AUTH_HOME` separately under the participating account's private
parent directory. It must not be a worker/helper/gateway profile. The prepared
image hash and Python bundle hash come from their checked build outputs. Supply
`DAIA_APPROVED_REQUEST_TEMPLATE` from the checked-in template described below;
these are explicit inputs, not values taken from a worker. The clean-checkout
helper creates its own `reviewed/runtime`; do not pre-create that same runtime
with the standalone example if you choose the clean-checkout route.

## Separate locked Python runtime

Use Python 3.12 and a trusted `uv` installation from the approved installation
side. Choose a new, absolute runtime destination outside any worker-writable tree.
From the trusted DAIA checkout:

```sh
UV_PROJECT_ENVIRONMENT="$DAIA_RUNTIME_DEST" uv sync --locked --no-editable --no-dev \
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
After the verifier succeeds, provision the base on a new host as follows:

```sh
test ! -e /var/lib/daia-lab/templates/base.qcow2
sudo install -m 0444 "$DAIA_BASE_IMAGE" /var/lib/daia-lab/templates/base.qcow2
printf '%s  %s\n' \
  612b2c0cc1bc413a6cb8c38fd611794caf0f2b436c50013d8b3794db12ad7354 \
  /var/lib/daia-lab/templates/base.qcow2 | sha256sum --check
```

Run these blocks in a shell with `set -eu`; a failed check must stop execution.
An existing base is inspected and verified, never silently overwritten.
A trusted installer must keep these bytes in protected template storage;
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
reviewed request template. The checked-in `codex-request-template.json` is the
Luna pilot's frozen policy and native tool catalog, with conversation history,
cache keys and client metadata removed. Its parsed gate authority was checked
identical to the template used in the successful trial. Review it as trusted
installation configuration; never approve an arbitrary first worker request.
For this exact client/model profile, set:

```sh
DAIA_APPROVED_REQUEST_TEMPLATE="$(realpath deploy/subscription-lab/codex-request-template.json)"
```

Do not harvest personal prompts
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
For the prepared-image route, use this clean preparation instead of the separate
runtime/fixture examples and select its outputs:

```sh
DAIA_RUNTIME_DEST="$DAIA_NEW_PREPARATION/runtime"
DAIA_SOURCE_FIXTURE="$DAIA_NEW_PREPARATION/source-fixture"
DAIA_NATIVE_FIXTURE="$DAIA_NEW_PREPARATION/guest"
cd "$DAIA_NEW_PREPARATION/source"
```

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
failure. Those packaging changes passed the replay tests. A subsequent live run fetched
all four required files from public commit
`321a1e9e87232566ce171913d7cf72dba6dc57a6`, verified their SHA-256 hashes, and
executed the public entrypoint from temporary RAM storage. Both the entrypoint
and its supervised guest returned zero; account/directory checks, nested KVM API
12, stopped service and removed overlay were reported. No provider or guest
network was used. Use normal Python as the trusted lab administrator.
This closes the public prerequisite-probe reproduction check, not installation
of QEMU/client/runtime inside the fresh host or a nested subscription worker run.

## Offline tool acquisition planning

From a trusted Ubuntu installation with authenticated, current APT metadata:

```sh
python3 scripts/plan_fresh_host_packages.py --output "$DAIA_PACKAGE_PLAN"
```

The planner uses an empty package-status file and `--print-uris`, so installed
host packages cannot silently satisfy the plan and nothing is downloaded or
installed. It requires SHA-256 records, preserves exact sizes/URLs in a new private
directory, and refuses duplicate filenames, unsafe names and credential-bearing
URLs. This does not independently authenticate APT metadata or acquire the pinned
Codex/client/DAIA Python artifacts. Do not publish the generated local plan.

Eight regressions passed. The existing native APT plan validated 115 records
(52,290,180 download bytes); APT estimated 215 MB of additional installed space
for these tools. No packages have been downloaded or installed by this step.
Recheck physical capacity before acquisition and installation.

## Rebuilding the direct-worker image (pilot candidate)

The trusted administrator can build a prepared image from local, reviewed inputs
with `scripts/prepare_fresh_host_image.py`. This step boots a networkless
installation VM, installs the supplied packages there, and exports its disk only
after the installation checks pass. It does not install those packages on the
participant's host, authenticate a provider or create assignment authority.

Image creation reuses the fresh-host acceptance fixture and checks nested KVM
inside that installation VM. The resulting direct worker runs as one VM; nested
VM execution is not part of a participant assignment. The reference build host
needs more than 5 GiB available RAM and the existing physical-disk reserve.

Supply the clean `source/` checkout and `prepared.json` produced by the existing
preparation flow. The recorded revision and lock hash must match that checkout;
executed scripts are snapshotted against their Git blobs. Supply Ubuntu's signed
checksum files, the exact base image, the package planner's `packages.json` and
matching downloaded archives, the approved Python wheel bundle and its SHA-256,
and the pinned Codex binaries. The builder performs no download. Protect all
inputs and their parent directories from worker writes.

Example with explicit administrator-selected paths:

```sh
sudo python3 scripts/prepare_fresh_host_image.py \
  --reviewed "$DAIA_NEW_PREPARATION" \
  --base-image "$DAIA_BASE_IMAGE" \
  --checksums /srv/daia/inputs/SHA256SUMS \
  --signature /srv/daia/inputs/SHA256SUMS.gpg \
  --package-manifest "$DAIA_PACKAGE_PLAN/packages.json" \
  --package-archives "$DAIA_PACKAGE_CACHE/archives" \
  --python-bundle "$DAIA_PYTHON_WORK/python.tgz" \
  --python-bundle-sha256 "$APPROVED_PYTHON_BUNDLE_SHA256" \
  --native /srv/daia/inputs/native \
  --iso-builder /usr/bin/genisoimage \
  --staging-root /var/lib/daia-lab \
  --output /srv/daia/prepared-image
```

The output directory must not already exist. The staging root must be traversable
by the dedicated runtime account and not writable by untrusted accounts; do not
change permissions on a personal home directory to satisfy this requirement.
After successful preparation, the output contains a read-only `host.qcow2` and
its recorded hash and `installation-report.json`. The report must confirm all
required package, Python/MCP, native-client and KVM checks before export. Temporary
installation storage is removed. The built image
contains no provider credentials. A second invocation creates a new output;
it does not overwrite or repair an existing image. Failed builds remove their
partial output and retain a private diagnostic file beside the requested output
directory for the administrator to inspect.

Use that exact image and SHA-256 with the direct worker's
`--prepared-host-image` and `--prepared-host-sha256` options. Worker READY must
still precede the finite assignment allowance. Successful image construction
alone does not establish subscription operation or release readiness: the
integrated task, independent evaluator, boundary and recovery gates remain
required on the candidate. This is a Linux/KVM pilot procedure, not a Windows
installer or authorization for public participation.


### Current prepared-image evidence and stopping point

The [15 September prepared-image pilot](../../docs/research/codex-clean-installation-pilot-2026-09-15.md)
completed one actual subscription development assignment and independently tested
its exact submitted source. The associated process-canary and gateway-loss probes
used that same image without START or provider calls. These results supersede
historical statements above that only prerequisite installation had been tested.

For this bounded pilot, use the reviewed Linux/KVM source and pinned inputs, build
and verify the prepared image as above, and complete official native login only
in the dedicated trusted provider profile. Keep that profile outside the image,
seed and worker account. READY must precede the existing finite assignment grant;
a slow boot is never permission to renew a deadline or replenish requests.

Stop after the assigned task and independently evaluate its exact stored artifact.
Use the recorded receipt recovery for the same submission only. Crash or host
reboot ends the old boot-bound model authority; reconnection is not permission to
resume it. Diagnose through trusted management and require a separately authorized
assignment before any new work. The tested host needed an operator to start SSH
after reboot, although unattended networking and remote management returned.

The tests cover the pinned, administrator-prepared pilot, not a one-click installer,
arbitrary workloads, general Windows support or proof against every VM escape.
Do not add personal profiles, host mounts, other MCP gateways or private network
routes to make an untested task work. General admission, production deployment
and merging the review stack remain separate decisions.


### Exact prepared-image launch

First derive the preboot variant of the approved native fixture, with a new
output directory. This creates the READY barrier used by the tested image path:

```sh
"$DAIA_RUNTIME_DEST/bin/python" scripts/prepare_preboot_fixture.py \
  --source "$DAIA_NATIVE_FIXTURE" --native "$DAIA_NATIVE_DIRECTORY" \
  --output "$DAIA_PREBOOT_FIXTURE" --iso-builder /usr/bin/genisoimage \
  --isoinfo /usr/bin/isoinfo
```

After successful image construction, read its recorded image hash:

```sh
DAIA_PREPARED_IMAGE_SHA256="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["prepared_sha256"])' /srv/daia/prepared-image/prepared-host-image.json)"
```

With the participant's existing,
separate native-login profile and the independently reviewed request template:

```sh
sudo "$DAIA_RUNTIME_DEST/bin/python" scripts/run_subscription_lab.py \
  --guest "$DAIA_PREBOOT_FIXTURE" \
  --request-template "$DAIA_APPROVED_REQUEST_TEMPLATE" \
  --auth-home "$DAIA_AUTH_HOME" \
  --codex-binary "$DAIA_NATIVE_DIRECTORY/codex" \
  --python-runtime "$DAIA_RUNTIME_DEST" \
  --native-delivery \
  --prepared-host-image "$DAIA_PREPARED_IMAGE" \
  --prepared-host-sha256 "$DAIA_PREPARED_IMAGE_SHA256"
```

This command consumes one explicitly authorized bounded assignment; do not run it
as an installation smoke test. It uses the current six-request/150-second model
limit, with a separate supervisor bound for preparation and cleanup. An error is
not permission to repeat the command or replenish the old assignment. Inspect
the private run metadata and existing receipt before deciding what to do next.
After successful supervisor completion, record the retained run path before a
reboot removes the transient pointer:

```sh
DAIA_COMPLETED_RUN="$(sudo python3 -c 'import json; print(json.load(open("/run/daia-subscription-run.json"))["state_directory"])')"
```

Keep that path in private operator notes. It is not a provider credential and
does not authorize resuming the run. After reboot, use the retained path rather
than assuming the transient pointer still exists.

### Acquiring the pinned native inputs

Use a new staging directory on the trusted Ubuntu amd64 installation host. The
[official Codex 0.153.4 release](https://github.com/openai/codex/releases/tag/rust-v0.153.4)
provides both native archives. Extract to stdout, not into the host filesystem;
the pinned digest must pass before a downloaded binary becomes executable:

```sh
set -eu
mkdir "$DAIA_NATIVE_DIRECTORY"
for name in codex codex-code-mode-host; do
  curl --fail --location --proto '=https' --proto-redir '=https' \
    "https://github.com/openai/codex/releases/download/rust-v0.153.4/${name}-x86_64-unknown-linux-musl.tar.gz" \
    --output "$DAIA_NATIVE_DIRECTORY/$name.tar.gz"
  tar -xOf "$DAIA_NATIVE_DIRECTORY/$name.tar.gz" > "$DAIA_NATIVE_DIRECTORY/$name"
done
printf '%s  %s\n' \
  56ef98ab4032d317ab26e9b5e5a175650717351edb16ed9cde0cb6d1734d62da "$DAIA_NATIVE_DIRECTORY/codex" \
  3e85d67471825f73d02ff5f7e047ca1f6ca8caa3f59e4c6e8d9ca6ca7302cb45 "$DAIA_NATIVE_DIRECTORY/codex-code-mode-host" \
  | sha256sum --check
```

The fixture's separate `bwrap` pin is the Ubuntu amd64
`bubblewrap=0.9.0-1ubuntu0.1` binary, not an automatically interchangeable Codex
release asset. Acquire it through authenticated Ubuntu APT metadata:

```sh
sudo apt-get install --no-install-recommends bubblewrap=0.9.0-1ubuntu0.1
cp /usr/bin/bwrap "$DAIA_NATIVE_DIRECTORY/bwrap"
printf '%s  %s\n' \
  52231e1caf55bcbc667b269f49c63599a6f7db4767ae6a039580d0ff853db712 "$DAIA_NATIVE_DIRECTORY/bwrap" \
  | sha256sum --check
chmod 0755 "$DAIA_NATIVE_DIRECTORY/codex" \
  "$DAIA_NATIVE_DIRECTORY/codex-code-mode-host" "$DAIA_NATIVE_DIRECTORY/bwrap"
```

If the exact version is unavailable or any digest differs, stop. Do not weaken
the pins, use `latest`, or execute an unverified replacement. The three builders
recheck the binary pins independently. Keep the native directory and ancestors
outside worker write access.

### Downloading the package plan

Generate `packages.json` with the planner above after authenticating the host's
Ubuntu APT metadata. Download that same dependency set into a new cache using an
empty dpkg status, so installed host packages cannot disappear from the plan:

```sh
set -eu
mkdir "$DAIA_PACKAGE_CACHE"
: > "$DAIA_PACKAGE_CACHE/status"
mkdir -p "$DAIA_PACKAGE_CACHE/archives/partial"
apt-get -o Acquire::ForceHash=sha256 \
  -o "Dir::State::status=$DAIA_PACKAGE_CACHE/status" \
  -o "Dir::Cache::archives=$DAIA_PACKAGE_CACHE/archives" \
  -o Debug::NoLocking=1 --yes --download-only --no-install-recommends install \
  qemu-system-x86 qemu-utils genisoimage python3-venv python3-pip
python3 - "$DAIA_PACKAGE_PLAN/packages.json" "$DAIA_PACKAGE_CACHE/archives" <<'PY'
import runpy, sys
helper = runpy.run_path('scripts/prepare_fresh_host_image.py')
helper['package_inputs'](sys.argv[1], sys.argv[2])
print('Exact package set, sizes and hashes verified; nothing installed')
PY
```

The check rejects extra/missing archives and metadata drift. Preserve the plan
with the downloaded archives. A changed plan is a new reviewed build input,
not permission to claim the previous image's acceptance results.

### Building the offline Python bundle

Run on the trusted Ubuntu amd64 host with Python 3.12, the reviewed checkout and
its unchanged `uv.lock`. Use a new absolute working directory and trusted `uv`.
These commands acquire/build installation artifacts; they run no task or model:

```sh
set -eu
mkdir "$DAIA_PYTHON_WORK"
mkdir -p "$DAIA_PYTHON_WORK/python/wheels"
uv export --locked --no-dev --extra mcp --no-emit-project --no-editable \
  --format requirements-txt --output-file "$DAIA_PYTHON_WORK/python/requirements.txt"
python3.12 -m pip download --require-hashes --only-binary=:all: \
  --dest "$DAIA_PYTHON_WORK/python/wheels" \
  --requirement "$DAIA_PYTHON_WORK/python/requirements.txt"
uv build --wheel --out-dir "$DAIA_PYTHON_WORK/dist"
cp "$DAIA_PYTHON_WORK/dist/daia_coordinator-0.1.0-py3-none-any.whl" "$DAIA_PYTHON_WORK/python/"
python3 - "$DAIA_PYTHON_WORK" <<'PY'
import hashlib, json, pathlib, sys, tarfile
root = pathlib.Path(sys.argv[1])
files = [root/'python/requirements.txt',
         root/'python/daia_coordinator-0.1.0-py3-none-any.whl',
         *sorted((root/'python/wheels').glob('*.whl'))]
manifest = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
record = root/'python/manifest.json'
record.write_text(json.dumps(manifest, indent=2)+'\n')
archive = root/'python.tgz'
with archive.open('xb') as output, tarfile.open(fileobj=output, mode='w:gz') as tar:
    for p in [*files, record]:
        tar.add(p, arcname=str(p.relative_to(root)), recursive=False)
print(hashlib.sha256(archive.read_bytes()).hexdigest())
PY
```

Review and retain that printed bundle digest with the source revision and lock
hash. Supply this archive and digest to `prepare_fresh_host_image.py`; its
`stage_python` check validates manifest coverage and every payload again before
installation. Never substitute a personal Python environment or credential home.

### Exporting and independently evaluating the recorded result

After the controller has stopped and cleanup is confirmed, select its exact
private run directory from its output. Export through the read-only helper; do
not query a different job, reconstruct a patch from terminal output, or resume
the model. The helper requires acknowledged delivery and verifies the recorded
assignment, envelope, artifact and receipt bindings before creating a new file.
It does not execute the exported source.

The following is for the version-comparison task used above. Run as the trusted
lab administrator, using new absolute output directories. The private export
stays separate from the readable evaluator bundle. The latter contains only the
candidate and fixed evaluator inputs, never provider credentials or run state.

```sh
DAIA_EVALUATION=/var/lib/daia-lab/evaluation-01
sudo mkdir -m 0755 "$DAIA_EVALUATION"
sudo mkdir -m 0700 "$DAIA_EVALUATION/private"
sudo "$DAIA_RUNTIME_DEST/bin/python" scripts/export_subscription_candidate.py \
  --run "$DAIA_COMPLETED_RUN" --output "$DAIA_EVALUATION/private/candidate.json"
sudo "$DAIA_RUNTIME_DEST/bin/python" scripts/prepare_version_evaluator.py \
  --candidate "$DAIA_EVALUATION/private/candidate.json" \
  --output "$DAIA_EVALUATION/seed" --iso-builder /usr/bin/genisoimage
sudo "$DAIA_RUNTIME_DEST/bin/python" - "$DAIA_EVALUATION" <<'PY'
import json, pathlib, subprocess, sys
root = pathlib.Path(sys.argv[1])
manifest = json.loads((root/'seed/evaluator.json').read_text())
subprocess.run([sys.executable, 'scripts/prepare_kvm_bundle.py',
    '--base', '/var/lib/daia-lab/templates/base.qcow2',
    '--base-sha256', '612b2c0cc1bc413a6cb8c38fd611794caf0f2b436c50013d8b3794db12ad7354',
    '--seed', str(root/'seed/seed.iso'), '--seed-sha256', manifest['seed_sha256'],
    '--nonce', manifest['nonce'], '--output', str(root/'bundle')], check=True)
PY
sudo "$DAIA_RUNTIME_DEST/bin/python" scripts/run_evaluator_lab.py \
  --bundle "$DAIA_EVALUATION/bundle" --output "$DAIA_EVALUATION/private/report.json"
sudo "$DAIA_RUNTIME_DEST/bin/python" - "$DAIA_EVALUATION" <<'PY'
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
source = json.loads((root/'private/candidate.json').read_text())
manifest = json.loads((root/'seed/evaluator.json').read_text())
report = json.loads((root/'private/report.json').read_text())
result = report['report']; guest = result['guest']
if not (report['ok'] is True and result['network_none'] is True
        and guest['nonce'] == manifest['nonce']
        and guest['source_sha256'] == manifest['source_sha256']
        == hashlib.sha256(source.encode()).hexdigest()
        and guest['cases_passed'] == 10 and guest['original_failed'] is True
        and guest['candidate_separate_uid'] is True
        and guest['parent_compares_results'] is True
        and guest['provider_credentials_present'] is False
        and guest['model_source_changed'] is False
        and result['overlay_removed'] is True):
    raise SystemExit('Independent evaluation not established; retain private evidence')
print('Exact recorded candidate passed all ten independent cases; overlay removed')
PY
```

Keep the private receipt and evaluation report as evidence. The evaluator removes
its transient writable VM storage; the explicitly created input bundle and
read-only base copy remain for inspection. Remove those build inputs when their
retention is no longer needed, without deleting the original run or credentials.
Ten passing fixture cases establish this task's result, not general code safety.
