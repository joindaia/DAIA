# Second-host subscription trial: failure retention

The bounded native Luna trial ended with a nonzero worker result. The supervisor
reported endpoint cleanup. A subsequent private inspection confirmed a different
WSL boot identity, an unconfirmed delivery outcome, and persisted model-authority
revocation. The ephemeral worker diagnostic had disappeared. No useful task,
provider-call count, or escape-test success can be claimed from this run.

The remaining-request ledger is not a usage report: revocation sets remaining
requests to zero regardless of how many reservations preceded it. The old run
must not be resumed or its authorization reset.

The controller now retains bounded stdout/stderr and the return code in the
existing private per-run directory, using atomic mode-0600 writes with fsync.
At model cleanup it also retains only the latest available gateway counters.
Missing or malformed counters are explicitly unavailable, never zero usage.
This counter snapshot is not proof of complete accounting after abrupt service
termination. No raw provider headers, tokens or response bodies are exported by
the counter helper. Worker diagnostics remain private and untrusted.

Validation: 32 outcome, authority and request-ledger tests passed locally. These
include bounded diagnostic retention after runtime-directory removal, private
file permissions, and exclusion of extra audit fields. The updated controller
has not yet been exercised on the second host. Abrupt controller termination
before retention can still leave diagnostics unavailable.

Next: install the reviewed change on the dedicated test host, then run a bounded
fresh diagnostic trial within existing participant authorization. First establish
useful native-client execution; the separately authorized Astra isolation trial
has not started. It will target synthetic canaries and designated lab services.
