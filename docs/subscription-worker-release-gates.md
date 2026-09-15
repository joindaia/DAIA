# Subscription worker release gates

Status: **experimental; not ready for general participant installation**.
Current evidence assessment: 15 September 2026. The latest complete second-host
cycle used runtime `096fa57244a723fa4564b49e2b856f8bc187a59c`. The review split
preserves that runtime tree exactly. Historical observations below retain their
original scope and dates; their outstanding-item lists are not the current backlog.

The original Codex 0.153.4 client completed a real Luna subscription development
cycle on the second host: public research, dependency use, a patch, source tests,
native MCP submission, exact retry, native credential refresh and normal supervised
shutdown. A fresh networkless evaluator passed ten cases on the exact submitted
source. This establishes the bounded lab route, not a general participant release.
See [the complete cycle](research/second-host-research-diagnostic-2026-09-15.md#completed-second-host-cycle-after-the-url-correction).
Claude, Gemini and local models are not prerequisites for the remaining work.

## Review order

Each PR is based on the preceding layer; review its own diff. All are drafts.
PR20 is closed without merge and retained as historical context.

| Order | Pull request | Review focus |
| --- | --- | --- |
| 1 | [#22](https://github.com/joindaia/DAIA/pull/22) | Request binding, response filtering and durable request limits |
| 2 | [#23](https://github.com/joindaia/DAIA/pull/23) | Provider transport, fixed upstream and bridge |
| 3 | [#26](https://github.com/joindaia/DAIA/pull/26) | Assignment-bound exact receipt recovery |
| 4 | [#27](https://github.com/joindaia/DAIA/pull/27) | Trusted installation prerequisites |
| 5 | [#28](https://github.com/joindaia/DAIA/pull/28) | Diagnostic experiments; not new runtime authority |
| 6 | [#29](https://github.com/joindaia/DAIA/pull/29) | VM preparation and independent networkless evaluation |
| 7 | [#24](https://github.com/joindaia/DAIA/pull/24) | Controller authority, lifecycle and result processing |
| 8 | [#30](https://github.com/joindaia/DAIA/pull/30) | Provider research and identity-binding limitations |
| 9 | [#31](https://github.com/joindaia/DAIA/pull/31) | Provider authentication and request-boundary evidence |
| 10 | [#32](https://github.com/joindaia/DAIA/pull/32) | Runtime isolation and recovery evidence |
| 11 | [#33](https://github.com/joindaia/DAIA/pull/33) | Task delivery and independent evaluation evidence |
| 12 | [#34](https://github.com/joindaia/DAIA/pull/34) | Technical runtime, request-gate and storage guides |
| 13 | [#25](https://github.com/joindaia/DAIA/pull/25) | Installation guidance and current release criteria |

## Evidence and outstanding acceptance

| Requirement | Current evidence | Remaining acceptance |
| --- | --- | --- |
| Original client and own subscription | Pinned native client; complete real second-host cycle linked above | Same route from a clean participant setup; no synthetic-response or paid-API substitution |
| Official login, refresh and restart | [Trusted profile preparation](research/native-profile-preparation-2026-09-13.json), [native lifecycle](research/second-host-native-auth-lifecycle-2026-09-13.json), refresh during the complete cycle | Integrate participant-operated initial login into clean installation; distinguish local unbinding from provider-side revocation |
| Credentials outside task execution | External credential service and assignment helper; complete cycle uses no guest provider credential | Malicious guest inspection of synthetic host credentials through files, processes, inherited handles and tool subprocesses in the packaged deployment |
| Inference-only account capability | Fixed upstream, discarded guest headers, bounded request fields and negative channel tests | Entire installed route: no alternate network path, unexpected gateway or inherited connector. Endpoint refusal is not exhaustive account confinement or provider approval |
| Host files and private networks | KVM/service separation; [loopback canaries](research/kvm-egress-canaries-2026-09-13.json), [DNS rebinding](research/kvm-dns-rebinding-2026-09-13.json), [mixed/CNAME checks](research/wire-dns-mixed-cname-2026-09-13.json) | Whole-worker synthetic browser/SSH/socket/file canaries and controlled live LAN/VPN targets, including redirects and DNS changes through every available tool path |
| Useful research, patching and tests | Complete second-host version task; [second outcome-summary task](research/outcome-summary-subscription-task-2026-09-13.json) independently evaluated, though its native turn needed bounded receipt recovery | General dependency installation/hooks and unattended completion across representative tasks remain unproven |
| Deadline, revocation and cleanup | Complete normal shutdown; [controller crash](research/kvm-controller-crash-2026-09-13.json); persistent revocation and overlay removal | Interruption and recovery of the complete clean installation, including host/controller restart, without resetting consent or budgets |
| Idempotent DAIA delivery | Native MCP exact retry stores one result; [pending recovery](research/real-native-pending-recovery-2026-09-13.json); [worker replacement](research/native-worker-crash-recovery-2026-09-13.json) | Partial-work checkpoints and controller/host reboot recovery remain open |
| Reproducible installation | [Repository controller](research/repository-subscription-controller-2026-09-13.json), public preparation scripts and [fresh dependency-cache preparation](research/clean-subscription-preparation-2026-09-13.json) | Fresh preparation reused trusted tools, image and request template; it did not provision a host or boot a guest. Demonstrate the entire route without pre-existing lab setup |
| Durable evidence | Public code and dated scoped reports; exact source/hash for the successful cycle | Tie the final installable candidate to all acceptance evidence; green CI and publication do not prove release readiness |

The fresh-host prerequisite probe now boots a networkless RAM-backed guest from
its pinned base, creates the four service identities with the public manifests,
checks directory modes and repeat provisioning, and verifies nested KVM API 12.
This does **not** install QEMU, the Python environment or Codex inside that fresh
host and does not boot a worker there. The offline APT plan identifies 115 packages
(52,290,180 download bytes) with SHA-256 metadata; no package download or
installation is implied. See the [installation record](../deploy/subscription-lab/README.md).

## Next acceptance sequence

1. Reproduce host provisioning and preparation using the public installation
   guidance and pinned inputs. Record which steps require the participant or an
   administrator. Existing lab accounts, templates or private setup scripts must
   not silently satisfy a clean-installation check.
2. Run the original native client with participant-authorized subscription access
   in that installation, then independently evaluate its exact submitted output.
3. Execute the whole-worker hostile host/account/network probes and lifecycle
   interruption tests against the same package. Observe refusals and cleanup from
   outside the worker; retain fixed consent, deadlines and request accounting.
4. Assess participant readiness only against those results. Do not repeat an
   unchanged positive lab fixture as a substitute for missing acceptance evidence.

These steps do not authorize new spending, outside contact, account sharing,
provider token pooling, increased consent or weakened security boundaries.

## Historical implementation and experiment log

The following entries describe the state when each experiment was recorded.
Use the current table above to identify what is still open.

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


### Original-assignment authority connected to the supervised lab

The lab controller now creates the six-request ledger after obtaining the actual
assignment and before starting the model gateway. Its private binding digest covers
the lease, original consent deadline, effective fixed model template, provider and
account. Only the digest is retained in the ledger metadata; no provider credential
is stored there. The model service receives its own private authority directory and
a read-only view of the kernel boot identifier, not the helper's state directory.
The original controller/helper time limits remain in place.

The actual model server now requires the retained authority; there is no missing-file
fallback to an in-memory budget. The service's ExecStopPost mode revokes that ledger
and removes its socket without loading provider credentials. The reproducible
`scripts/probe_authority_service_cleanup.py` starts a private-network service, proves
its child reserved one request, kills that child with SIGKILL, then confirms zero
remaining authority and socket removal by the real stop handler. No provider is
contacted by that probe. Thirty-eight affected preparation and boundary tests passed.

One actual native Codex/Spark subscription task then completed with five provider
requests, 23 channel denials, native refresh/restart with unchanged account/deadline,
one stored result and normal supervised cleanup. Post-run inspection confirmed that
the persistent ledger matches the recorded assignment binding, has private permissions
and model-service ownership, and is zero with a successful stop-handler marker.
These persistence checks were inspected separately after the run; the supervisor's
normal success report still primarily checks process and endpoint cleanup.

A fresh networkless evaluator tested the exact stored source, hash
`5ef4ed11594272559631333856d2b55e7dca9e7cdeb9d4b5eeda31e9dac2c242`:
ten cases passed and the original fixture failed. Candidate code ran under a separate
UID; the trusted parent compared results. No provider credentials were present in
the evaluator and its overlay was removed. [Evidence](research/wired-request-authority-2026-09-13.json).

This establishes the ledger's use in the existing lab, not successful recovery of
an entire controller or host. A stopped gateway deliberately leaves its authority
revoked. Safely resuming unfinished work, retaining prior credential-reflection
patterns, automated post-stop authority verification, clean participant installation
and the broader worker/network acceptance gates remain open. No limits were increased.


### Supervisor success requires verified durable revocation

The supervisor now verifies the retained authority after the controller service
returns and before writing a successful assembled result. The controller records
its exact service identity in private run metadata. Verification requires that
identity, matching binding digests, integer zero remaining authority and a completed
revocation marker. It reads bounded regular files through no-follow directory
handles and checks owners, permissions and hard-link counts. Endpoint cleanup or
a marker alone no longer satisfies the success condition.

Fifty-two affected tests passed, including rejection of stale-controller records,
missing or contradictory markers, nonzero/boolean budgets, wrong binding/owner,
shared paths, symlinks, hardlinks, FIFOs and oversized records. Valid inspection
leaves the records unchanged. The updated real service-crash probe reserved a
synthetic attempt, killed its child, ran the actual stop handler and passed this
same supervisor verification with zero authority and no model endpoint remaining.
No model credentials or provider calls were used for these checks.
[Evidence](research/supervisor-revocation-gate-2026-09-13.json).

This closes the previously manual post-stop authority check in the supervisor
code. The entire native subscription task has not been repeated after adding this
final success gate; the preceding live result remains evidence for the ledger
wiring, and this service probe covers the new verification separately. Historical
run records without the controller identity are rejected rather than upgraded.
Full controller recovery, host-reboot recovery and participant installation remain
open, and no new resume permission follows from a successfully revoked run.


### Preparation cannot move the original authority deadline

The controller now freezes a CLOCK_BOOTTIME cutoff when calculating the original
remaining allowance and passes that absolute cutoff to authority preparation.
The binding digest includes it. Ledger creation caps its deadline against this
cutoff before opening/writing the state file; filesystem delay no longer restarts
the relative duration. Existing callers without a cutoff also freeze their deadline
before file creation. Expired or invalid supplied cutoffs create no authority.

Forty request-ledger, authority, shutdown and crash-rendezvous tests passed.
Injected clock advancement during file opening preserved the original cutoff and
caused reservation at that cutoff to fail. The actual isolated service-crash probe
still reached reservation before SIGKILL, durably revoked its ledger and passed
the supervisor check. No provider calls occurred. The complete native subscription
run was not repeated for this deadline change. Full recovery and clean participant
installation remain unestablished.
[Evidence](research/frozen-authority-deadline-2026-09-13.json).


### Full regression and explicit Linux boundary checks

At commit `322b5a6`, the complete default test suite passed 667 tests with ten
explicit skips and one Starlette/AnyIO deprecation warning. The opt-in real Linux
namespace suites then passed nine tests, and the original hash-pinned Codex command
sandbox probe passed using an empty configuration/credential home. These counts
overlap; they are not additional distinct tests to sum into the default count.
The two Windows file-sharing checks and Nginx runtime check remain unexecuted here.

The current service-account/directory manifests also passed their real systemd
installation probe against an empty temporary filesystem root, including repeat
installation, four distinct nonroot accounts and five directory checks. Host
accounts were unchanged. No provider credentials or model requests were used.
[Evidence](research/subscription-integration-regression-2026-09-13.json).

These results establish regression coverage and the finite tested Linux command,
namespace and manifest behaviours. They do not certify the entire agent environment,
private LAN/VPN isolation, clean participant installation or full crash recovery.

## Second useful task and its incomplete native turn

The [outcome-summary task](research/outcome-summary-subscription-task-2026-09-13.json)
produced a real subscription-backed addition to the operator result module.
Seven independent networkless evaluator cases passed; the maintainer reviewed the
exact addition and connected it to read-only multi-run inspection. Thirty-three
targeted regressions passed and the live two-run summary worked. Request authority
was durably revoked after the worker stopped.

The native turn consumed its six requests before retrying the intentionally lost
receipt. One result was already persisted; the existing bounded recovery route
recovered that exact receipt without model use or consent changes. Do not mark
native unattended completion, generalized development or separate-host installation
as satisfied by this trial. Earlier unsuccessful attempts are included in evidence.


## Assignment helper handles one lost receipt without another model turn

An installer-selected helper option now retries the same saved signed submission
once within a single MCP tool call. It leaves the existing identity, consent,
assignment and request allowance intact. The real coordinator/MCP regression
returned `already_recorded`, with one stored result and cleared pending state.
Eighty-eight regressions passed; two Windows-only tests were skipped.

Two bounded subscription attempts exhausted six forwarded requests before result
submission, so they did not reach this helper path. They are failures, not proof of
native completion. The final failed run's persisted model authority was verified
revoked. Expanded private diagnostics were truncated; compact metadata-only
diagnostics have been prepared for the next useful investigation. Do not repeatedly
run unchanged trials or infer that increasing budgets is authorized by this result.
See [scoped evidence](research/assignment-helper-receipt-retry-2026-09-13.json).


### Second host: confirmed native delivery and independent evaluation

On 15 September the prepared second host completed a real Luna development
contribution after two narrow native-protocol compatibility fixes. Four provider
responses produced one stored result, with heartbeat, a deliberately lost receipt
and an exact acknowledged retry. A separate networkless evaluator passed ten
cases on unchanged stored source while the original failed. Model authority was
persistently revoked and all lab services stopped.

The client received 403 after delivery and exited nonzero, so normal whole-worker
completion remains open. Existing login and prepared artifacts were reused; this
is not the clean-participant installation or full hostile-worker acceptance gate.
See the [follow-up](research/second-host-failure-retention-2026-09-13.md#follow-up-on-15-september-useful-result-incomplete-client-shutdown)
and [sanitized evidence](research/second-host-subscription-compatibility-2026-09-15.json).


### Second host: complete bounded cycle after documentation correction

The follow-up at `096fa57244a723fa4564b49e2b856f8bc187a59c` completed normal
native and supervised-controller exit, public research, dependency use, unchanged
source tests, native MCP delivery and exact receipt retry within six model
requests. Native credential refresh preserved the deadline; persistent authority
revocation and storage cleanup were verified. A fresh networkless evaluator
passed ten cases on the exact stored source while the original failed.

The cause of the preceding research failure was a documentation URL now returning
301. The fix uses its direct 200 destination on the same allowed host; it adds no
redirect following or broader network authority. See the
[complete cycle and exact source](research/second-host-research-diagnostic-2026-09-15.md#completed-second-host-cycle-after-the-url-correction).
Clean participant installation and comprehensive hostile-worker/account acceptance
remain open. No general release or admission decision follows from this fixture.
