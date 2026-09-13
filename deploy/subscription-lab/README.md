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
