# Codex subscription pilot on the reproducible installation

## Evidence status

A real original Codex client completed the bounded development assignment on the
reproducibly built Linux/KVM installation. The coordinator stored one result,
the assignment helper recovered a deliberately lost receipt, and a separate
networkless evaluator accepted the exact submitted source. This is a technical
pilot result, not public-release approval or a product-value benchmark.

The remaining acceptance gates are explicitly open below. Earlier lab results
are supporting evidence and do not replace current-candidate acceptance.

## Candidate and bounds

- Runtime source: `53e22c86a31e77fc0b15e1563e01ab3bd4fbdaa9`.
- Staged source manifest identifier: `68ca08463081b926`.
- Prepared installation image SHA-256:
  `416cc0dc84fb6cc242f857f6c3295ca5696dbdc04fc7b7d13b49f409fc42dddf`.
- Task/preboot seed SHA-256:
  `08c1cc9ce81d83ab68c31b01b7f4d5fa8aa39581fb202b3f49c8951e146be0e8`.
- Original Codex version: `0.153.4`; model: `gpt-5.6-luna`.
- Maximum six provider requests and 150 seconds of model access. Preboot READY
  precedes task authority. No old grant, identity or request ledger was reset.
- The prepared image is a clean-host acceptance fixture, not an additional VM
  layer required of participants. Task changes were delivered by a separate seed.

The image was built without provider credentials. Its earlier installation check
covered isolated service identities, required directories, KVM availability,
offline native-client checks and repeat installation. This run reused that image.

## Successful development and delivery

The task required public documentation research, correction of numerical version
comparison, unchanged supplied tests and native MCP submission. The final source
uses the standard library; this task did not require a third-party dependency.

The controller completed in 70.19 seconds with five forwarded provider requests,
five attempts and 23 denied probes. The last provider response was HTTP 200.
It recorded:

- native credential refresh and client restart after the first provider request;
- unchanged provider account and preserved deadline;
- unchanged contributor identity and finite consent;
- one coordinator result;
- a first committed submission whose response was deliberately hidden;
- an exact retry returning `already_recorded`, clearing pending delivery state;
- revocation and no active DAIA services after cleanup.

The native client made one heartbeat call and one submission call. The trusted
assignment helper performed the exact transport retry within that submission
call. This distinguishes two remote submission attempts from two model calls.
The helper does not obtain another assignment, alter the artifact, extend consent
or make another inference request to recover a receipt.

## Independent evaluation

The evaluator read the exact stored artifact, checked its hash and assignment
binding, and tested the source in a fresh VM without network or provider
credentials. Candidate execution used a separate UID; the evaluator parent
compared results. All ten cases passed, while the original source failed.

Exact evaluated source SHA-256:
`608dd7508ec7067790274e4ef5baf652501864c54311072d5c72e726c4b5443a`.

The evaluator did not change the submitted source. Its overlay was removed and
no DAIA services remained active. Evaluation made zero provider requests.
This establishes correctness for the fixture's ten cases, not general software
correctness or an independent assessment of DAIA's productivity.

## Current-candidate boundary checks

Separate real-VM probes used the same staged runtime and installation image:

| Check | Observed result | Limit |
|---|---|---|
| Host file, mounts, sockets and auth paths | Guest probes denied; host-readable synthetic canary unchanged | Specific tested paths, not proof against every kernel escape |
| Assignment discovery | Exactly `heartbeat` and `submit_result`; empty resources, prompts and templates; unknown method/resource refused | Synthetic host without task authority; zero provider requests |
| Direct private-network probe | Live listeners established before QEMU; two positive controls; zero unexpected guest connections | Direct TCP test, not comprehensive DNS/redirect coverage |
| READY-stage controller crash | Real QEMU and private marker existed before SIGKILL; dependent VM stopped, cgroup empty, recorded processes gone, private files removed | Pre-authority crash; not equivalent to every active-job crash |

All four probes completed successfully without sending START or using provider
credentials. The development run additionally recorded six denied research
requests. Full provider/account and network coverage must be assessed against
the individual probes, not inferred from these aggregate counts.

## Failed attempt retained

An earlier run on the same image used a fixture with helper receipt retry disabled.
It forwarded six requests, committed a result, then failed to recover the deliberately
hidden receipt. Its independently evaluated source passed ten cases, but its
controller and receipt-recovery status remain failed. It was not relabeled as
successful or resumed with replenished authority.

The correction enables the existing bounded helper retry and changes the fixture
instructions accordingly. Nine focused receipt/bundle tests passed. The builder
also accepts the existing native-derived fixture without duplicating MCP setup.

## Open release gates

A controlled physical-host restart was requested only after unattended network
access and automatic management services were verified. A synthetic, nonempty
ledger was prepared beforehand. At the latest observation the host had not
returned over its management connections. Therefore host-reboot recovery has
**not** passed; no explanation for the missing connection is asserted.

Before completing this pilot:

1. Reconnect and verify the original pre-reboot ledger, without recreating it.
2. Finish the requirement-by-requirement audit of real-token isolation, unwanted
   provider operations, network paths, revocation and active-authority crash
   recovery on the current candidate. Do not substitute the READY crash test.
3. Confirm current CI and complete the reviewable installation/evidence stack.

No main merge, production deployment or public admission is authorized by this
report. Private diagnostic transcripts, host identifiers, accounts and credentials
are intentionally excluded.
