# Guest assignment transport

Status: Linux worker integration primitive, not a complete worker installer.

`python -m daia.assignment_guest` runs inside a prepared disposable VM. It connects
once to the fixed virtual assignment endpoint `10.0.2.100:3128` and relays the
native client's stdio MCP traffic. The trusted launcher must map that address to
one already-assigned helper outside the guest. Do not install this as a host-side
MCP helper or expose the general contributor interface through that route.

The adapter reuses `assignment_relay.relay`: a 30-second connection lifetime and
256 KiB combined byte budget, with queued data drained before EOF propagation.
Connection setup has an eight-second timeout. It returns 124 on relay expiry and
1 on connection or transfer failure. There is no reconnect or unconfined fallback.
The limits suit a short submission session, not an hour-long persistent MCP session.

The adapter contains no invitation, signing key, consent management or destination
selection interface. It is transport code, not an isolation boundary: the VM,
network mapping, separate helper identity and independent lifecycle controls must
be supplied outside it. The helper must enforce the pinned assignment regardless
of changes made to this adapter inside the untrusted guest.

## Verification

The local subprocess/socket regression proves that closing model input propagates
EOF while preserving the final helper reply. Existing relay tests cover stalled
peers, deadline enforcement and the combined byte budget:

```sh
PYTHONPATH=src python -m pytest tests/test_assignment_guest.py tests/test_assignment_relay.py -q
```

A private KVM integration trial used native Codex with this adapter, the real
assignment-bound helper outside the VM, and synthetic coordinator/model fixtures.
After a committed submission lost its response, a changed retry was rejected and
an exact retry returned the persisted receipt. Independent helper checks found one
result, unchanged key/consent/usage and cleared pending state after the exact receipt.
This is observed lab evidence, not a repository-contained VM test or verification
of existing participants, provider-account isolation or production deployment.
