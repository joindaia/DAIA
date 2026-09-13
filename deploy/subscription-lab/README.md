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
  --extra dev --extra mcp --python /usr/bin/python3.12
```

The current experimental controller imports repository test helpers, so `dev` is
still required. Keep the approved checkout available; this is not yet a standalone
controller wheel. `--locked` refuses lock drift and `--no-editable` installs the
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
