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
