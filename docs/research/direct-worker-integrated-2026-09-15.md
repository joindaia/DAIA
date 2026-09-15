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

## Limits and remaining acceptance

The source changed after the successful development task to repair crash cleanup.
The affected normal-completion path still needs validation on that final candidate.
The earlier failed task attempt that submitted a result but lacked a successful
VM report remains a recorded failure; its original diagnostic was truncated, so
its root cause is not claimed to be established.

Before closing the release goal:

1. Complete exact direct-worker host-file/credential-path and private-network
   canary tests. Older standalone or Docker-based probes do not prove this route.
2. Finish capability enumeration and compare each exposed operation with the
   allowed assignment, model and research interfaces.
3. Execute controlled host-reboot recovery, proving that old nonempty, unexpired
   synthetic authority is refused rather than automatically resumed.
4. Validate affected paths on the final source candidate, publish a reproducible
   installation procedure and keep code/evidence in reviewable pull requests.

There is no implicit main merge, production deployment, public admission or
claim that all provider-account functions have been exhaustively tested.
