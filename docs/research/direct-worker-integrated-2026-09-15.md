# Direct worker integration: measured results and remaining gates

Status: experimental pilot candidate, not a release or public-admission approval.
Measured on 15 September 2026. The successful task used one disposable KVM guest,
the original Codex 0.153.4 client and a real participant subscription. Credentials
and assignment signing remained outside the guest. These results do not establish
isolation against every possible attack or support for arbitrary host platforms.

## Successful integrated task

The source staging manifest was `b5e630f5478da768`. This is the test harness's
truncated SHA-256 identifier over its per-file source manifest, not a Git commit
or a cryptographic release attestation. Source changes are under review.

The prepared image SHA-256 was
`3ba1d1b043a37b6946826e611c4b10172967c2825416922e8de5b7010cfbc606`.
The worker reached READY before the controller created finite assignment/model
authority. The unchanged allowance was six requests and 150 seconds. Preparation
was outside that allowance; it did not reset or extend assignment time.

Observed results:

- The complete supervised run exited successfully after 130.21 seconds, including
  preparation. Five requests were forwarded; 23 negative model requests were denied.
- Native Codex retrieved 773,941 bytes of public documentation and obtained the
  `packaging` 25.0 wheel. Import and dependency checks succeeded. Six negative
  research requests were denied.
- Native MCP heartbeat, submission and exact retry after an intentionally lost
  receipt produced exactly one stored result. A stored result alone was not used
  as proof of successful worker completion.
- Native credential refresh and client restart completed after the first provider
  request. Account binding and the original deadline were preserved.
- The supplied tests were unchanged. The worker exited successfully, the overlay
  was removed, model authority was revoked and no DAIA service remained active.
- A separate networkless evaluator received the exact stored source, verified its
  assignment binding and hash, and passed ten cases. The original implementation
  failed. Candidate execution used a separate user from the comparison process;
  the model-produced source was not changed by the evaluator.

Artifact source SHA-256:
`7e5e9f1b3a4211d93b6892af5b8037fb9933d9e33415dfdb6fee8725a254dfb8`.

Documentation SHA-256:
`d275c6ee8f8a3112710a37c7581af56cef2e322d9ea05263fb422bd4c642fb1a`.

Dependency wheel SHA-256:
`29572ef2b1f17581046b3a2227d5c611fb25ec70ca1ba8554b24b0e69331a484`.

The complete successful report is retained atomically in the private run directory.
An earlier successful run's detailed volatile report disappeared after a host
restart. Its summary and evaluator were retained, but those were insufficient to
reconstruct every detailed check; it is not substituted for this evidence.

## Crash results and the repair they required

A credential-free direct-worker test reached READY, externally observed QEMU and
an in-guest-runtime synthetic marker, then killed only its test controller.
The initial implementation stopped all recorded processes and removed private
working storage, but left the control directory. The test failed even though its
observer subsequently removed that directory.

The repair places the control directory under the parent service's systemd
`RuntimeDirectory`. Source staging manifest `0cedf526b7e8268f` passed the repeat:
the parent reached its terminal state, the bound prepared service stopped, the
cgroup was empty, every recorded process disappeared, private working storage was
gone and the control directory was automatically removed. No START, assignment
allowance, provider credential or model request was involved.

Separately, the same candidate's actual model-service stop handler was tested
with a synthetic allowance. A reservation occurred before SIGKILL. The handler
persisted revocation, set remaining requests to zero and removed its endpoint;
the supervisor's revocation check passed. This is service-level evidence, not a
substitute for host-reboot or guest-network tests.

## Direct guest boundary checks

The host-file probe ran before START on staging manifest `462c9a4b18bc45b6`.
A synthetic host file existed and was readable to the external observer. Guest
root could not open that path directly or through a symlink, or open the fixed
host credential path. No credential contents were read or exported. Selected
host mounts, SSH-agent and Docker sockets were absent. The host canary hash was
unchanged after the test, and no DAIA service remained active. These observations
cover the tested paths, not every possible filesystem attack.

The direct TCP probe on staging manifest `5aa1322fd0d509a8` placed a fixed test
listener in the actual prepared QEMU service's private network namespace before
QEMU started. Independent positive controls succeeded both before and after the
guest probe. The guest could not connect through the QEMU host address; the
listener observed zero unexpected connections. READY and cleanup succeeded.
No START, provider credentials or model requests were used. A timeout alone was
not accepted as evidence: both external positive controls were required.

This proves the tested direct network path, not the full DNS, redirect, IPv6 or
provider-account capability surface. The normal worker network configuration
was unchanged; the listener was test instrumentation only.

## Normal completion after the cleanup repair

Staging manifest `5aa1322fd0d509a8` completed the same real subscription task in
141.26 seconds including preparation, with five forwarded requests, 23 model
request denials and six research denials. The allowance remained six requests
and 150 seconds. Native exit, turn completion, unchanged tests, MCP delivery and
exact lost-receipt recovery succeeded with exactly one stored result. Native
refresh and client restart preserved the account and deadline. Revocation and
supervised cleanup passed with no remaining DAIA services.

A fresh networkless evaluator tested the exact stored artifact without changing
its source: ten cases passed, the original failed, candidate execution used a
separate user from the comparison process, and cleanup succeeded. It made no
provider calls. Artifact source SHA-256:
`e99bc34e516ce55e489d23b4612793cba34482c12e78075151e8d895a0b1322b`.

The documentation fetch remained 773,941 bytes; its content hash in this run was
`9ba7786ddb62e294f094b3c8e52b8cc40647c121cd1ffcc3c9eb8a3285b2648f`.
The dependency wheel hash was unchanged. A preceding attempt on staging manifest
`0cedf526b7e8268f` stopped on an upstream header timeout. It remains a failed run,
with authority revoked; the subsequent task did not extend or resume its budget.

Source inspection confirms the gateway compares the request's canonical
`additional_tools` catalog with the frozen template before forwarding. Successful
inference therefore passed that policy. This is distinct from claiming every
provider account endpoint was individually tested.

## Limits and remaining acceptance

The cleanup repair now has a successful normal-completion run and an independent
evaluation. Installation packaging and the remaining acceptance items below are
still incomplete.
The earlier failed task attempt that submitted a result but lacked a successful
VM report remains a recorded failure; its original diagnostic was truncated, so
its root cause is not claimed to be established.

Before closing the release goal:

1. Reconcile remaining network cases with the direct-worker evidence above.
   Older standalone or Docker-based probes do not prove this route.
2. Finish capability enumeration and compare each exposed operation with the
   allowed assignment, model and research interfaces.
3. Execute controlled host-reboot recovery, proving that old nonempty, unexpired
   synthetic authority is refused rather than automatically resumed.
4. Validate affected paths on the final source candidate, publish a reproducible
   installation procedure and keep code/evidence in reviewable pull requests.

There is no implicit main merge, production deployment, public admission or
claim that all provider-account functions have been exhaustively tested.
