# Second-host research and completion diagnostics — 15 September 2026

These are separate follow-up trials to the [earlier independently evaluated
contribution](second-host-subscription-compatibility-2026-09-15.json). They do not
replace that evidence or establish complete subscription-worker acceptance.
Both used the original pinned Codex 0.153.4 client, `gpt-5.6-luna`, a fresh KVM
worker and the existing external credential boundary. Runtime baseline:
`0b65e151911292e905428ed4919b89aeb3d1fd40`.

| Observation | Completion diagnostic | Research diagnostic |
|---|---:|---:|
| Provider attempts | 5 | 6 |
| Completed forwards | 5 | 5 |
| Gateway denials, including 23 intentional negative probes | 23 | 24 |
| Native turn completed | Yes | No |
| Delivery | Acknowledged | Unconfirmed |
| Complete worker acceptance | Failed | Failed |
| Duration, seconds | 83.88 | 133.85 |
| Previous run's ledger unchanged | Yes | Yes |
| Persistent model revocation verified | Yes | Yes |

The first follow-up passed the native completion checks but failed because the
required research result file was absent. Inspection confirms that preparation,
research and validation use matching paths. The recorded evidence does not
establish whether research was omitted or failed. A submitted source artifact is
not a substitute for this required task step; no new independent evaluation is
claimed for this trial.

The next trial added research-stage diagnostics. It failed earlier, with a client
403 after the sixth provider attempt, so its post-client research check was never
reached. Five forwards and six attempts locate an unsuccessful operation after
entry into the forwarding path; they do not identify its cause. A transient audit
showed the last observed provider status was 200, but that does not prove the sixth
response completed successfully. The transient audit was no longer available on
subsequent inspection. No definite timeout, quota exhaustion or policy mismatch
is inferred. No active lab services remained after the trial.

The research diagnostic trial used these additional fixture hashes:

- Guest probe: `33521d42f82fd2c7134adad008e67d8afa531e1dcf1b9c0088fac7cf6b35bef4`.
- Research script: `9dce333d6036b2318e6ea869acf2f5d361566105d7673b71d957e41802c0019c`.
- Prepared guest seed: `0dc5379987f3b2f9f7a16cead3546a5335cf7daf2acad5758ec7680888f55ad8`.

## Change after the trials

The fixture now exports research file/stage diagnostics before reporting a native
client failure, as well as when the research result cannot be read. The external
controller retains only allowlisted upstream failure categories, transport
phase/kind and the last observed HTTP status alongside its counters. It does not
retain arbitrary provider error text, tokens or request bodies through this path.
All guest diagnostics remain untrusted private evidence, not acceptance proofs.

Twenty focused tests passed covering fixture assembly, failure retention and
outcome handling. Diagnostic tests execute only maintainer-controlled snippets
with synthetic inputs and temporary paths; they do not start a guest or execute
candidate code or downloaded dependencies on the host. This final diagnostic
revision has **not yet been tested live**.

Next: use a fresh bounded trial with the complete diagnostic revision to determine
whether research started and which stage failed, and distinguish forwarding
failure from later native completion failure. Keep the six-request/150-second
model limits, source tests, research requirement and external verification intact.
Never reset old authority or resubmit an already accepted result to obtain a pass.

## Concrete documentation failure and correction

A subsequent trial of `66bc00c074da2f83c62c5d6c5b02f7e1a2cefeea`
completed five provider forwards/attempts with only the 23 intentional denials.
The native client exited successfully and delivery was acknowledged, but the
research helper recorded `documentation` / `AssertionError`. No documentation
file had been written. Whole-worker acceptance therefore remained failed.

Direct HTTP checks with the fixture's User-Agent on both the development host
and second host established the cause: `/3/library/stdtypes.html` now returns
301 to `https://docs.python.org/3/builtins/stdtypes.html`. The new URL returns
200 directly and 773,941 bytes, within the unchanged 1,000,000-byte limit.
These were credential-free HTTP checks, not a successful guest trial.

PR #24 changes only the fixed path in the research fixture and standalone
research probe. It adds no redirect following and does not widen the allowed
hosts, limits or TLS behavior. Ten local fixture/bundle tests passed. The fresh full subscription-worker trial of this correction is recorded below.

## Completed second-host cycle after the URL correction

The fresh trial of `096fa57244a723fa4564b49e2b856f8bc187a59c` completed
the controlled numeric-version development task in 129.76 seconds. The original
Codex client used the participant subscription; no simulated model responses
were substituted. The prepared guest seed was
`3cc301f07898c3aa524e10a02cfcfa9e4443846b9b7a822e4edd73ab6ffc4c38`.

| Required observation | Result |
|---|---|
| Native client and supervised controller exit | Both zero |
| Provider attempts / completed forwards | 6 / 6 |
| Intentionally forbidden requests rejected | 23 |
| Documentation downloaded | 773,941 bytes |
| Downloaded dependency | packaging 25.0; digest checked, imported and exercised |
| Supplied source tests | Unchanged |
| Native assignment MCP calls | Three: heartbeat, submit, identical receipt retry |
| Stored results / acknowledged delivery | One / yes |
| Native credential refresh | Completed; original deadline preserved |
| Worker storage and model authority | Overlay removed; persistent revocation verified |
| Independent evaluator | Ten cases passed; original implementation failed |
| Evaluator boundary | Fresh networkless VM; no provider credentials; separate candidate UID |
| Post-evaluation cleanup | Overlay removed; no active lab services |

The evaluator read the exact stored assignment artifact, checked its digest and
assignment binding, and compared results in its trusted parent process. The model
source was not changed. Its SHA-256 is
`26ea50db31fe1435faf8d28ecbae6746d861993d37855a0de557362623aee62e`:

```python
def newer(a, b):
    def normalize(value):
        parts = [int(component) for component in value.split(".")]
        while len(parts) > 1 and parts[-1] == 0:
            parts.pop()
        return parts

    left, right = normalize(a), normalize(b)
    length = max(len(left), len(right))
    left += [0] * (length - len(left))
    right += [0] * (length - len(right))
    return left > right
```

This closes the bounded second-host development-cycle check. It does not prove
arbitrary task correctness, a clean participant installation, exhaustive hostile
worker/account confinement, or provider endorsement. Existing login and prepared
lab infrastructure were reused. The earlier failed trials remain separate evidence.
