# Subscription worker release gates

Status: **experimental; not ready for general participant installation**.
Assessment on 2026-09-13 against commit `04523ca`. This is an evidence map,
not a replacement objective or permission to reduce the remaining scope.
A successful fixture run proves its recorded scope, not every deployment.

The original Codex client has completed a real Spark subscription development
fixture inside KVM with outside-guest authentication, native refresh, public
research, a recorded result and independent evaluation. The next work is to make
that complete route reproducible and to close the remaining boundary tests.
Claude, Gemini and local models are not prerequisites.

## Evidence and outstanding acceptance

| Requirement | Current evidence | Remaining acceptance |
| --- | --- | --- |
| Original client and own subscription | [Pinned client and live trial](research/packaged-channel-subscription-trial-2026-09-13.json); original 0.153.4 binary, actual Spark calls | Pin the installable bundle and validate the same route from a clean participant setup; do not substitute synthetic responses or paid API access |
| Official login, refresh and restart | [Native refresh](research/native-subscription-refresh-2026-09-13.json), followed by refresh during the live assignment | Package the native trusted-side login lifecycle; distinguish local unbinding from provider-side revocation |
| Credentials outside task execution | Separate model service and fixed HTTPS transport used by the lab; assignment helper state excluded from other service identities | Repeat malicious guest inspection against synthetic host credentials across filesystem, process state, inherited handles and tool subprocesses in the packaged deployment; no token exposure may be accepted as success |
| Inference-only account capability | Fixed upstream route, discarded guest headers and native identifiers, frozen non-history fields, local tools only; negative channel tests | Verify the entire installable network/account path has no bypass, unexpected gateway or inherited connector; route refusal alone is not exhaustive account confinement or provider approval |
| Host files and private networks | Separate KVM/service identities; [real loopback canaries](research/kvm-egress-canaries-2026-09-13.json) and [real UDP DNS change](research/kvm-dns-rebinding-2026-09-13.json) | Broader synthetic host/browser/SSH/socket canaries, live controlled LAN/VPN targets, mixed/CNAME/redirect paths and the complete guest tool environment |
| Useful research, patching and tests | Real public documentation fetch, wheel import and model patch; independent networkless evaluator passed ten cases on identical submitted bytes | General dependency installation and installation hooks remain unproven; repeat a task beyond this small version-comparison fixture |
| Deadline, revocation and cleanup | Request/deadline bounds in upstream; TLS revocation tests; [real controller crash](research/kvm-controller-crash-2026-09-13.json) and normal supervised cleanup | Exercise interruption/recovery of the complete installable route; retain external watchdogs and immutable task limits |
| Idempotent DAIA delivery | Changed retry rejected, exact retry retained one stored result; source matched independent evaluator | Native Codex MCP delivery and exact retry now have a [live subscription result](research/native-subscription-mcp-delivery-2026-09-13.json), with independent evaluation of the stored artifact. A [real failed-run pending receipt](research/real-native-pending-recovery-2026-09-13.json) was recovered without new work or model calls. A [live worker replacement](research/native-worker-crash-recovery-2026-09-13.json) now completes from original input with the same gateway budget and consent, followed by independent evaluation. Partial-work checkpoints and controller/host reboot recovery remain open |
| Reproducible installation | Core channel and tested server/guest fixtures are in the repository | Full launcher still depends on private lab scripts, runtime templates and service setup. A clean installation must work without those private paths or pre-existing lab state |
| Durable evidence | Test fixtures, scoped reports and code are on the research branch | Keep new reports tied to the exact tested bundle and candidate; do not confuse publication of a fixture with installation readiness |

## Next implementation sequence

1. Bring the complete Linux launcher into a reviewable repository package. Inventory
   the live harness's actual dependencies first: pinned base/client images, seed
   generation, separate service identities, credential-free approved task input,
   fixed relays, external native-auth refresh and supervisor cleanup. Remove
   implicit private paths and pre-existing state; retain the existing limits.
2. Recreate that package from a clean lab directory and run the existing positive
   fixture with the unchanged independent evaluator. Missing dependencies must
   fail before task execution; never fall back to host execution or broader rights.
3. Run hostile host/account/network probes against that same package, then crash
   and recreate its worker while recovering the exact pending assignment/result.
   Verify cleanup externally and preserve original consent and receipt semantics.
4. Only after these gates pass, consider participant installation. Public admission,
   unattended deployment and broader provider-account guarantees are not implied
   by the present lab results.

These steps do not authorize new spending, outside contact, account sharing,
provider token pooling, increased consent or weakened security boundaries.

## First launcher extraction

The [restricted KVM start component](kvm-launcher.md) now verifies the base, seed
and all three bridge digests before disk creation, streams image hashing and
refuses the host network namespace. A real credential-free boot and negative
preflight checks passed. This does not yet package service setup, authentication,
seed generation, disk quotas or receipt recovery.

## Regression baseline

Full Linux suite at `04523ca`: **546 passed, 10 skipped, one warning**, in 60.93 s.
The skipped checks are one opt-in native Codex sandbox test, six opt-in namespace
isolation tests, two Windows file-sharing tests and one Nginx integration test.
They are **not** counted as passing in this run. The warning is a dependency's
AnyIO `BlockingPortal` deprecation. The separately recorded KVM trials are live
integration evidence; the general suite does not replace them or prove Windows
support. No current GitHub CI result is asserted by this local measurement.


## Updated regression run

At `7ad84f5`, before the development-fixture extraction: **567 passed, 10 skipped,
one warning**, in 63.28 seconds. The skips retain the native Codex, namespace,
Windows sharing and Nginx integration boundaries listed above. The warning is
the same AnyIO dependency deprecation. This is local regression evidence, not
a current GitHub CI result or completion of the live release gates.


## Explicit Linux boundary integrations

The previously opt-in namespace/MCP checks were run explicitly: nine passed with
`DAIA_RUN_ISOLATION_TESTS=1`. A strengthened host-loopback test first establishes
a real control connection, then checks both failure inside the sandbox and absence
of a connection at the external listener. The pinned original Codex binary also
passed the corresponding clean-home command-sandbox test with
`DAIA_RUN_CODEX_SANDBOX_TESTS=1`; it now includes external listener observation.
No provider credential or model request was used.

See [live command boundary evidence](research/live-command-boundaries-2026-09-13.json).
These are actual namespace/process tests, not skipped checks counted as success.
They support the specific command boundaries and assignment socket rules; they
do not close whole-worker, comprehensive private-network, account-capability or
clean-installation release gates. Windows and Nginx skips remain separate.


## Mixed-address gateway canaries

The public-egress canary was rerun in a dedicated loopback-only network namespace.
Six pure-private or mixed public/private resolver-answer sets were rejected before
any outgoing connect attempt. Real IPv4/IPv6 listeners accepted 24 control
connections and zero gateway connections. Thirty targeted tests passed. The probe
now refuses to bind listeners when any interface other than loopback is present.

See [mixed-address evidence](research/mixed-dns-canaries-2026-09-13.json). Resolver
answers in this probe are synthetic; the sockets and namespace are real. This
does not add wire-DNS/CNAME or redirect/browser coverage and does not certify the
full worker network. Those release gates remain open.


## Real DNS packets for mixed answers and CNAMEs

`probe_wire_dns_egress.py` now exercises the real libc resolver against a local
UDP DNS fixture, without replacing `getaddrinfo`. Run only inside a dedicated
network and mount namespace with loopback enabled, namespace-local aliases
`1.1.1.1/32` and `2606:4700:4700::1111/128`, and a private bind-mounted resolver
file containing `nameserver 127.0.0.1`. Do not change the host resolver or routes.
The script refuses a non-loopback interface before creating listeners.

The actual run made twelve A/AAAA queries. A public destination and a public
CNAME succeeded; mixed A, mixed AAAA, public A plus private AAAA, and a private
CNAME failed. Twenty-four direct control connections proved all TCP canaries
reachable; zero unexpected connections arrived. Thirty-one regression tests
passed. After the test the host did not use the lab resolver.

See [wire DNS evidence](research/wire-dns-mixed-cname-2026-09-13.json). The CNAME
target records were included in the same DNS answer. This does not prove recursive
or multihop CNAME behavior, redirects, a browser's full path, or KVM integration.
There were no model/provider calls or external routes.


## Service identity preflight

Both subscription lab entrypoints now reject missing, root or duplicate service
identities and reject a worker socket group shared with another lab identity.
The check includes supplementary group membership and runs before state cleanup,
bundle creation or credential access. Previously the startup path only established
that the account names existed; separate names alone do not imply separate UIDs.

The existing lab configuration passed the read-only check. Sixteen targeted
identity, outcome, crash-rendezvous and retained-run tests passed. No accounts
were changed and no provider call occurred. See [evidence](research/subscription-service-identity-preflight-2026-09-13.json).
This is one installation prerequisite, not a clean installer or proof of effective
service confinement. A trusted administrator can still change account state after
the preflight; immutable installation and effective runtime checks remain needed.


## Private authentication file reads

The lab controller now opens the dedicated profile directory and `auth.json`
without following final-component symlinks. It validates the opened descriptors:
private modes, matching owner, regular single-link file and a bounded one-MiB
read. The profile may not belong to any worker, helper or gateway service account.
Refresh reads must preserve the original owner; malformed content is rejected
without echoing credentials. A FIFO cannot block this read. Native atomic file
replacement under the same trusted profile remains supported.

Twenty focused authentication and identity tests passed, using synthetic tokens.
No live provider refresh or model request was performed for this change.
[Evidence](research/subscription-private-auth-read-2026-09-13.json) records the
scope. Ancestor directories and the native client's own profile access remain
part of the trusted installation boundary; this is not proof against a malicious
profile owner or administrator changing files concurrently.


## Live confirmation after authentication preflight changes

At `3e9ac9f`, the existing bounded lab completed a fresh original-Codex Spark
subscription run with six successful provider requests, 23 denied requests,
native refresh/restart and unchanged account/deadline. One result was stored,
pending delivery cleared, and supervisor cleanup completed. No limits changed.

A fresh networkless evaluator then tested the exact stored source bytes: all ten
version-comparison cases passed while the original implementation failed. The
source hash matched the coordinator artifact; no normalization or source edit
was introduced. Evaluator temporary storage was removed. See [live evidence](research/private-auth-live-subscription-2026-09-13.json).

This closes the live compatibility check for the new identity/profile readers.
It does not establish a clean participant installation, broader task usefulness,
complete account/network confinement, or recovery after controller/host reboot.


## Declarative account and directory installation

[Native systemd manifests](../deploy/subscription-lab/README.md) now define the
four separate lab accounts and required state/socket directories. The repository
probe ran sysusers and tmpfiles against an empty temporary root twice: four
distinct nonroot identities and five directory owner/mode checks passed; repeated
account files were identical and the host account files remained unchanged.
No credentials or running services were involved. [Evidence](research/lab-installation-basis-2026-09-13.json).

This is an actual fresh-root provisioning check, not a full participant install.
It leaves runtime/image/client provisioning, trusted first login, existing-state
migration and complete execution under newly installed identities open.


## Fresh locked Python environments

At `52fbe20`, two empty runtime destinations were populated from the unchanged
lockfile with a non-editable DAIA installation. The first required missing cached
artifacts to be downloaded; the second then completed offline. Both contained
the same 39 distribution versions. An isolated import and CLI help worked outside
the checkout. The full source suite in the new runtime passed 596 tests, skipped
ten integrations/platform checks and emitted one dependency warning (64.10 s).

[Build instructions](../deploy/subscription-lab/README.md) and [evidence](research/clean-locked-runtime-2026-09-13.json) record the exact boundary. The controller still
uses approved repository/test helpers, and a full VM run on the new runtime has
not occurred. This removes the need to copy the old Python environment; it is not
yet complete participant installation or a vulnerability audit.


## Full lab run on the newly built Python runtime

At `8630596`, the controller and isolated assignment helper used the newly built
locked runtime instead of the old development environment. The existing real
Codex subscription fixture completed in five provider requests, with 23 denials,
native refresh/restart, unchanged account/deadline, one stored result and complete
supervised cleanup. A fresh networkless evaluator passed all ten cases on exactly
the stored source; the original failed and evaluator storage was removed.

[Evidence](research/fresh-runtime-live-subscription-2026-09-13.json). This confirms
runtime replacement in the complete lab chain. It still reuses host identities,
the base image/client fixture, trusted login and approved checkout/test helpers.
The clean participant installation and broader adversarial gates remain open.


## Lab controller no longer imports test modules

The controller now creates its contributor using the real loopback MCP endpoint
instead of a test replacement for remote calls. The small local-server, invite
and authorization setup lives in `subscription_lab_fixture.py`; the controller
no longer adds the tests directory or imports pytest-dependent test modules.
This remains trusted finite lab setup, not production registration authority.

A fresh locked runtime without the dev extra installed 31 distributions. With
pytest absent, the actual HTTP claim, heartbeat, committed-but-lost submission
and exact retry completed with unchanged identity/consent and one result.
Thirty-five targeted tests passed. [Evidence](research/lab-without-test-imports-2026-09-13.json).
The changed controller has not yet completed a full VM/subscription run. The
approved source checkout is still required; this does not finish packaging.


## Failed no-dev runtime integration trial

The first full VM trial at `6cd9569` reached the provider but did not complete its
first response: one attempt, HTTP 200, zero completed forwards, and 24 denials
including the failed call. The controller exited nonzero, delivery was unconfirmed,
and supervised endpoints/handoffs were removed. No automatic retry, renewed
budget or independent artifact evaluation was authorized. [Evidence](research/no-dev-runtime-transport-failure-2026-09-13.json).

The old generic transport error does not identify whether timeout, socket failure
or HTTP framing caused this incident. Do not infer a specific cause from HTTP 200.
The adapter now records fixed operator-only phase/kind categories, never exception
text or provider bytes; the worker still receives the same generic denial. Sixty-five
transport regression tests passed, including secret-bearing exceptions and consumed
failed-attempt budgets. No transport limit changed and no second provider run was
performed. Full no-dev runtime subscription acceptance remains open.


## Diagnosed body timeout and completed no-dev runtime trial

A fresh diagnostic run at `7da7eb7` recorded HTTP 200 followed by a **body timeout**
on its first provider attempt. This identifies that run's transport failure; the
earlier generic incident remains less specific. The same five-second timeout had
been applied to connection setup and reading model output.

Connection setup remains bounded to five seconds. Body inactivity is now bounded
to at most thirty seconds, capped by the remaining original assignment deadline.
The independent watchdog, six-request budget, response-size limits and failed-call
accounting are unchanged. A controlled provider delayed its body 5.5 seconds and
completed under the original ten-second test deadline; all 66 transport tests passed.

One fresh corrected subscription trial completed using the runtime without pytest
and real MCP claim route: six provider requests, 23 denials, native refresh/restart,
one stored result and complete cleanup. A separate networkless evaluator passed
ten cases on identical stored source while the original failed, then removed its
temporary storage. [Evidence](research/subscription-body-timeout-2026-09-13.json).

This confirms the changed no-dev lab chain and a bounded handling improvement for
slow model output. It does not make arbitrarily slow requests succeed or remove
the remaining clean-installation, account and network release gates.


## First-login profile preparation

A trusted-side preparation tool now verifies the pinned original binary and
creates an exclusive private profile without copying credentials or starting a
login. The documented next step is a separate participant-run native device-code
flow with a cleared environment. Five negative/positive tests passed; the real
pinned client's login help worked against a temporary prepared profile and left
no auth file. [Evidence](research/native-profile-preparation-2026-09-13.json).
The full first login still requires participant interaction and was not repeated.
This does not replace the outside-worker credential/account boundary.


## Native authentication checks survive optimized Python

A regression reproduced a bypass in `probe_codex_native_auth.py`: Python `-O`
removed assert-based checks and allowed an unapproved synthetic binary (including
a symlink) to start beside a synthetic profile. Both cases failed before the fix.
All checks in this probe now use explicit runtime guards, including the final
lifecycle verification, so optimization cannot erase them.

Twenty targeted tests passed after correction. A separate check using the actual
pinned client and a nonprivate empty profile also refused startup under `-O`
before any login. No real credentials or provider request was used.
[Evidence](research/native-auth-optimized-checks-2026-09-13.json). This fixes this
probe's optimization bypass; it is not an audit of all lab scripts or a new live
refresh result. Trusted installation/path assumptions still apply.


## Lab entrypoints reject optimized execution

The supervisor, controller, assignment helper, subscription gateway and two
installation/receipt probes now reject `not __debug__` immediately after their
module docstrings, before imports or side effects. Their remaining lab assertions
therefore cannot silently disappear under `-O` or `PYTHONOPTIMIZE=2`. The native
authentication probe separately uses explicit checks and supports optimization.

Twelve real subprocess refusals across six entrypoints passed, alongside the
identity, credential and crash-rendezvous regressions: 36 tests in total. No service
or provider call started. [Evidence](research/lab-optimized-execution-refusal-2026-09-13.json).
This is not an all-repository assertion audit or proof about arbitrary guest code.
Normal execution is unchanged; full VM execution was not repeated for this guard.


## Base-image origin and offline verification

The existing base hash now has a reproducible dated source and an offline verifier.
Fresh Ubuntu 20260911 checksum/signature metadata verified against the system
cloudimage keyring, and the existing 625256960-byte image matched the exact pinned
hash. Altered metadata and a wrong image were refused; seven verifier/bundle tests
passed. [Evidence](research/verified-base-image-origin-2026-09-13.json).

The verifier neither installs nor boots the image and will not accept a newer
image automatically. Trusted keyring installation, vulnerability review and the
complete clean-host installation still need their own evidence.


### Fresh fixture preparation through native subscription delivery

The two repository fixture builders were run into new directories and their
output used in a live native Codex subscription run. Five provider requests
completed; refresh/restart preserved the account and deadline; one result was
stored with pending delivery cleared, and supervised cleanup completed. A fresh
networkless evaluator processed the exact stored source and reported ten passing
cases while the original failed. This is a separate execution check, not proof
that arbitrary malicious code cannot falsify guest test reports.

See [evidence](research/fresh-fixture-chain-2026-09-13.json) and the
[rebuild commands](../deploy/subscription-lab/README.md#rebuilding-the-approved-development-input).
Existing authentication and trusted installation artifacts were reused; the full
fresh-host installation gate remains open. No admission or runtime limits changed.


### Real HTTPS redirect transport probe

The credential-free `scripts/probe_https_redirect_egress.py` runs curl with
certificate verification through the actual research CONNECT handler. In a
private network/mount namespace a synthetic public-address HTTPS server returned
redirects. The allowed public redirect completed; private IPv4/IPv6 hostnames,
a literal IPv4 address and an unlisted hostname each failed with proxy 403.
All five initial HTTPS requests and the positive follow-up reached the server.
Ten direct canary control connections succeeded; no canary connection arrived
through the proxy. No provider calls or host network changes were made.

Reproduce only in a disposable network/mount namespace: make mount propagation
private, bind a test hosts file over `/etc/hosts`, bring up loopback, add
`1.1.1.1/32` to loopback, and run the script with the approved DAIA source on
`PYTHONPATH`. The hosts file must map `public.daia.invalid` to `1.1.1.1`,
`private4.daia.invalid` to `127.0.0.1`, and `private6.daia.invalid` to `::1`.
The script requires curl and openssl, generates a temporary test certificate and
removes its key when finished. Do not apply these aliases or hosts mappings to
the ordinary host network. The script refuses non-loopback network interfaces.

[Recorded results](research/https-redirect-egress-2026-09-13.json) establish this
real client/TLS/CONNECT redirect route, not browser behavior, wire DNS, live
LAN/VPN isolation or the complete worker deployment. TLS payloads remain opaque
to the research proxy; account confinement on shared hosts is a separate gate.


### Evaluator pass/fail is outside candidate execution

Review found that the previous evaluator imported candidate code into its test
process and treated exit status zero as success. `sys.exit(0)` could skip the
assertions. The corrected guest parent invokes each case in a fresh process as
`nobody` and requires an actual JSON boolean matching the expected value. Empty,
malformed or incorrect output is rejected. The candidate cannot write the
root-owned source/checker or serial report endpoint. Candidate code still executes
only inside a fresh networkless KVM, never on the installation host.

The data fixture `tests/fixtures/evaluator-false-success.json` was built with
`prepare_version_evaluator.py`, bundled with `prepare_kvm_bundle.py` and run with
`run_evaluator_lab.py`. A real KVM run rejected it with `Candidate result mismatch`
and returned failure; cleanup completed. The exact previously stored Codex patch
was separately evaluated again and passed all ten cases, with the original failing.
Seven offline preparation/bundle tests passed. No new model request was used.
See [evidence](research/evaluator-process-separation-2026-09-13.json).

This strengthens the evaluator without rewriting historical results: earlier
runs did not have this separation. It does not prove general correctness beyond
the finite cases or protect against guest kernel compromise. Further hostile
attempts against the report channel and checker remain necessary.

The first positive run failed with QEMU `qemu_thread_create: Resource temporarily
unavailable` and cleaned up. A new run of the same bundle succeeded without
raising process, memory or time limits. The resource failure's cause remains
unproven; it is retained in the evidence and is not counted as a passing test.


### Guest evaluator tampering probes

The synthetic data fixture `tests/fixtures/evaluator-tamper-attempts.json` was
prepared and run through the existing seed/bundle/networkless evaluator commands.
Before returning a correct result for each of ten cases, it successfully writes,
reads and deletes a temporary guest file, then requires permission denials for
checker/script writes, serial output, parent stdout through `/proc`, a checker
symlink, SIGSTOP against the privileged parent and a serial write in a child
process. The real KVM evaluation passed all ten guarded cases and the original
failed. Cleanup completed; no provider requests occurred.

[Evidence](research/evaluator-tamper-attempts-2026-09-13.json) relies on this fixed,
trusted attack fixture executing as specified, not a hostile contributor's claim
that their tests passed. It strengthens the finite permission-boundary evidence;
it does not establish kernel security, exhaustive report-channel enumeration or
the complete research-enabled worker boundary. Seven preparation/bundle tests
also passed; pytest could not write its cache in the read-only test invocation.


### Installed Python runtime advisory audit

The separately installed pip-audit 2.10.1 checked the actual no-dev subscription
runtime using PyPI advisories: 30 external distributions, zero reported known
vulnerabilities. The local DAIA distribution was explicitly skipped. Every
installed name appeared in the report and every installed version matched the
lock. No runtime dependency was changed. See [audit evidence](research/subscription-runtime-advisory-audit-2026-09-13.json).
This closes only this dated Python-runtime lookup; source review, other software
layers and a fresh pre-release audit remain required.


### Rotation preserves response filtering for retired credentials

A local TLS regression exposed a response-filter gap: after trusted rotation,
only the current bearer token was checked. A literal reflection of the previously
used token was returned by the HTTPS adapter. The regression failed before the
fix and passed afterward. The shared adapter now keeps the byte patterns of all
credentials issued to that short-lived binding and rejects their literal presence
in provider output. Only the current token is used for outgoing authentication.
The patterns remain outside the worker and are not written to a log or journal.

All 109 HTTPS, upstream and channel tests passed. The new tests cover current and
retired token reflections, unchanged deadline, consumption of the rejected call,
a succeeding clean response and denial when the original request budget is spent.
See [evidence](research/retired-credential-response-filter-2026-09-13.json).

This is a synthetic local TLS test, not a new live subscription run. Literal
filtering is defence in depth, not a proof against encoded, fragmented or otherwise
transformed secret disclosure by a hostile provider. Provider-side revocation of
old tokens, controller/host reboot recovery and the full release gates remain
separate requirements. No consent, provider quota or worker access was expanded.


### Persistent request accounting before gateway recovery

The fixed HTTPS adapter now accepts an optional trusted `request_authority`
(path, binding digest). When provided, `request_ledger.reserve` durably decrements
the original allowance before socket creation. This Linux ledger uses a private
regular file, nonblocking process lock, fsync before forwarding, a boot identifier
and CLOCK_BOOTTIME deadline (including suspend). Existing files cannot be recreated
by `create`; missing, corrupt, shared, linked, expired, wrong-binding or different-boot
records deny rather than establish a fresh allowance. Failed provider requests
consume their reserved attempt. No provider credential is stored in the ledger.

123 targeted tests passed. A real child process reserves an attempt and exits
abruptly; a fresh process consumes only the remaining attempt. Eight concurrent
processes cannot collectively exceed three attempts. A local TLS test creates
three successive HTTPS adapters: one succeeds, one receives a provider error, and
the third is denied without a connection despite its new in-memory allowance.
[Evidence](research/persistent-request-accounting-2026-09-13.json).

**Integration status:** the live supervisor does not yet supply this authority.
It is an available transport boundary, not working full-controller recovery.
Legacy lab calls retain their existing in-memory limits; no new resume command is
introduced. Before enabling recovery, the trusted controller must create the record
once, bind its digest to the original assignment/account/template/consent, preserve
its location and permissions across replacement, supply access to the real boot ID,
and never silently fall back to no ledger. The worker must have no access to its
path, creation or replacement. Explicit revocation must remain durable too; the initial
ledger tests established accounting and expiry only; the following section adds
persisted manual revocation.

Recovery must also retain credential-reflection protection for previously used
credentials outside the worker, validate original consent, and reconstruct helper
state without creating a new assignment. A host reboot is deliberately denied by
this ledger rather than translating deadlines or authorizing fresh work. File
fsync and process-crash tests do not prove storage behaviour under power loss or
protect against an administrator rolling back the state. These remain explicit
limits; the full release gate stays open.


### Durable revocation before controller recovery

The trusted ledger can now irreversibly set the matching authority's remaining
allowance to zero. Repeated revocation is safe, including for already expired or
previous-boot records, without changing their binding or deadline. A different
binding cannot revoke another record. A fresh process cannot reserve a request
from the revoked record.

The HTTPS adapter stops its local active socket before attempting persistence.
A storage or lock failure raises a denial to an explicit caller and leaves
`revocation_persisted` false. The expiry watchdog also keeps local execution stopped
on persistence failure; its status must be checked by the trusted supervisor. A
controller must not treat stopped local I/O as proof of durable revocation, or
restart another gateway after an unconfirmed write. This does not cancel a request
already sent by a different gateway process; supervisor termination of the old
service remains necessary before replacement.

128 targeted tests passed. The new local TLS probes include interruption of a
continuously streaming response with both successful and failed fsync, denial on
the original adapter, an explicit persistence retry after the injected failure,
and refusal by a freshly constructed adapter without a new TLS connection. A
separate process test verifies that persisted revocation prevents reservation.
[Evidence](research/persistent-request-revocation-2026-09-13.json).

These are synthetic tests with no external provider calls. The live supervisor
still does not configure the ledger, and complete controller/host recovery remains
open. Persisted ledger revocation is local DAIA authority removal, not provider-side
OAuth token revocation. No broader consent or provider use was introduced.
