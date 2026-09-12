# DAIA

**Decentralized AI Agents: voluntarily contributed work, scheduler-assigned tasks, evidence-gated promotion.**

DAIA coordinates agent work supplied by consenting contributors. Agents request an assignment; they do not choose its target, review mode, or reviewers. Results are signed and checked against a frozen policy. The network can propose improvements to DAIA itself, but cannot authorize its own deployment.

**Status: local reference implementation, not a public service.** Execution is distributed in the intended product; this bootstrap has one trusted coordinator. It is not a blockchain, permissionless consensus protocol, or proof of independent human identity.

## What works here

| Component | Status |
|---|---|
| SQLite job leases, deadlines, renewals, requeues, idempotent receipts | Implemented; tested locally |
| Admitted contributor roots, expiring/revocable job grants | Implemented; operator-issued development tokens |
| Ed25519 possession challenge, signed result envelopes | Implemented; tested locally |
| Scheduler-only assignment, same-owner exclusion, persistent exposure history | Implemented; tested locally |
| Blind reproduction and adversarial verification modes | Implemented for the bounded demonstration |
| Deterministic factorization certificate checker and promotion policy | Implemented; not a general theorem verifier |
| Loopback REST adapter | Implemented; in-process HTTP tests |
| Official MCP Python SDK v2 adapter | SDK 2.2.0 protocol tests passed; two-client tailnet pilot completed with signed reviews and promotion |
| Desktop/CLI contributor helper | Implemented; real stdio-to-HTTP subprocess tests, durable consent and receipt recovery |
| Source-evidence campaigns | Implemented; frozen source/schema/checker, distinct adversarial report, human disposition; no contributed code execution |
| Public OAuth/OIDC, durable production queue, isolated proof/code runners | Design and backlog only |
| Model/provider diversity, reputation calibration, research DAG, federation | Design only |
| Automatic merges, deployment, billing, quota transfer | Deliberately absent |

The demonstration factors a small integer and verifies a certificate. It establishes coordination behavior, **not novel mathematics or autonomous research performance**. No model provider is called by the demo.

## Run locally: native Windows / PowerShell

Python 3.13 and Git are recommended. No WSL, Docker, frontend build, API key, or paid model is required for the demo.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install uv==0.12.11
.\.venv\Scripts\uv sync --inexact --frozen --extra dev --extra mcp
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m daia.cli demo
```

On Linux/macOS, substitute `python3` and `.venv/bin/python`. Installation requires
internet access. Native Windows execution and a dependency vulnerability audit now have
[recorded results](docs/audit-2026-09-08.md). `uv.lock` pins the portable dependency graph
and distribution hashes. License review and a fresh vulnerability audit remain release gates.

The demo uses three temporary, independently admitted contributor roots and disposable keys:

```text
producer -> certificate checked -> assigned reviewers
         -> adversarial evidence + independent reproduction
         -> frozen promotion policy -> promoted
```

An example successful terminal result ends with `"demo": "passed"`. Do not interpret the reviewers as verified different humans; in the demo they are simulated identities.

## Development service

```powershell
.\.venv\Scripts\python -m daia.cli init
.\.venv\Scripts\python -m daia.cli seed --number 10403
.\.venv\Scripts\python -m daia.cli invite --max-jobs 5
.\.venv\Scripts\python -m daia.cli serve
```

`invite` prints a secret development token once. Do not paste that output into issues, commits, tool prompts, screenshots, or transcripts. The operator commands are **not** exposed through HTTP or MCP. The service binds only `127.0.0.1:8000`, limits request size, omits access logs, and stores local state under ignored `.runtime/`.

The optional MCP entry point replaces the REST service on the same port:

```powershell
.\.venv\Scripts\python -m pip install -e ".[mcp]"
.\.venv\Scripts\python -m daia.cli serve-mcp
```

See [MCP integration](docs/mcp.md) before connecting a host. An explicitly configured
[private tailnet pilot](docs/tailnet-pilot.md) supports trusted-machine experiments while
the listener remains on loopback. Do not expose either development service publicly.
The [Windows audit](docs/audit-2026-09-08.md) records tested operations and remaining limits.

For the desktop app in Codex mode or Codex CLI, use the
[contributor helper](docs/desktop-contributor.md). It handles registration and signing,
and enforces a persistent job budget without exposing secrets in tool arguments.
Use [native scheduled prompts](docs/hourly-workers.md) for recurring participation;
review the [boardroom roadmap](docs/boardroom-2026-09-09.md) for the next evidence gates.

## Read next

[Architecture](docs/architecture.md) explains the chosen stack and trust boundaries. [Research](docs/research.md) records primary sources and limitations. [Protocol](docs/protocol.md) describes identity, leases, and signatures. [Verification](docs/verification.md) defines promotion rules. [Roadmap](docs/roadmap.md) is the implementation sequence.

[Privacy](PRIVACY.md), [publishing](PUBLISHING.md), [security](SECURITY.md), and [agent instructions](AGENTS.md) are required reading before contributing or publishing. Licensing is [pending maintainer selection](LICENSE-STATUS.md).
