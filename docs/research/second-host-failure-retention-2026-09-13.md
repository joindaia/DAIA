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


## Follow-up on 15 September: useful result, incomplete client shutdown

The updated controller retained second-host failure diagnostics as intended. A
first run stopped before any provider attempt because the pinned native client
sent `x-openai-internal-codex-responses-lite`. Accepting and discarding that exact
header fixed the transport mismatch; no guest header reaches the upstream.

Two subsequent runs each completed one provider response, then rejected a local
custom-call history item. A private diagnostic probe recorded only fixed source
locations. Credential-free native captures reproduced that Codex executes both
qualified `functions`/`exec` and bare `exec`. The corrected gate accepts the bare
form only when the frozen top-level and deferred tool declarations resolve it
uniquely to the already-approved `functions.exec`. Null/foreign namespaces,
flat dotted names and conflicting declarations remain rejected. Static review
found no authority expansion; 163 focused tests passed.

A fresh subscription run at `0b65e15` completed four provider forwards and stored
one result. The native helper heartbeated, submitted, lost the first confirmation
and retried identically; the second receipt was `already_recorded`. A read-only
check established acknowledged delivery and persisted model-authority revocation.
The client then received a further 403 and exited nonzero. This is useful native
work with confirmed delivery, **not** successful whole-worker completion.

A fresh networkless evaluator ran the exact stored source without modification:
ten cases passed and the original implementation failed. Candidate execution used
a separate guest user; the parent compared the results. Temporary evaluator
storage was removed and no DAIA services remained active.

[Sanitized evidence](second-host-subscription-compatibility-2026-09-15.json) records
the separate trials and limits. Next: diagnose the post-delivery refusal and
establish normal bounded shutdown without extra authority or duplicate submission.
The clean-installation and broader adversarial release gates remain open.
