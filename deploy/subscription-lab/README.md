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
