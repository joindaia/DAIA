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
| Idempotent DAIA delivery | Changed retry rejected, exact retry retained one stored result; source matched independent evaluator | Native Codex MCP delivery and exact retry now have a [live subscription result](research/native-subscription-mcp-delivery-2026-09-13.json), with independent evaluation of the stored artifact. A [real failed-run pending receipt](research/real-native-pending-recovery-2026-09-13.json) was recovered without new work or model calls. Still prove unfinished-work recovery through a newly created guest without changing consent or resetting the model budget |
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
