# Architecture and stack decision

Decision date: 2026-09-08. Status: proposed production architecture with a working local reference core.

## Product contract

The donor authorizes a bounded contribution. The existing agent host performs inference using its own supported provider integration. DAIA supplies jobs and receives artifacts, not provider passwords or subscription sessions. Donors retain the right to stop or decline unsafe work. They may eventually choose broad consent categories; they must not select individual jobs, candidates, review modes, or reviewers.

The bootstrap uses an operator-granted **number of assignments** and an expiration time. These are real enforceable server limits. They are not a claim to know or enforce a percentage of any provider's subscription quota. A host-side clock or provider cost ceiling is a different control.

## Components

```text
Contributor-controlled agent host and signer
        | MCP / authenticated requests / consent grant
        v
Coordinator boundary
  authenticated contributor -> assignment engine -> lease
  signed result -> receipt ledger -> frozen promotion policy
        |                                ^
        |                         typed reviewer evidence
        v                                |
Trusted, isolated deterministic verifier / benchmark runner
        |
Evidence-gated candidate -> separate maintainer / release boundary
```

The coordinator does not execute submitted shell commands, load uploaded modules, train a model, or connect to donor account sessions. The local built-in checker reads bounded JSON data only.

## Recommended stack

| Layer | Choice | Reason and boundary |
|---|---|---|
| Core | Python 3.13, typed domain services | One language for scheduling, research tooling, validation, and tests; native Windows development |
| Agent interface | Official MCP Python SDK, Streamable HTTP | Use a supported protocol rather than a proprietary worker daemon; optional adapter until interoperability tests pass |
| Operator/development API | FastAPI + Pydantic | Strict request schemas; domain services remain independent of transport |
| Local persistence | Python SQLite | Zero-install development; serialized transactions, not a production scaling claim |
| Production persistence and queue | PostgreSQL 18, explicit SQL / psycopg, reviewed migrations | Atomic grants, conflict checks, leases, uniqueness, and transactional outbox; no Redis dependency initially |
| Identity | Established OAuth/OIDC service for access; Ed25519 for artifact provenance | Authorization and cryptographic attribution solve different problems |
| Artifacts | Bounded DB text initially; private object storage later | Introduce S3-compatible content-addressed storage only when artifact size warrants it |
| Proof/code verification | Pinned Lean toolchain or test harness on isolated runners | Never run untrusted proof build scripts or code beside coordinator secrets |
| Observability | Aggregate counts first; OpenTelemetry later | No prompt/token/body logging by default; privately scoped, short-lived diagnostics |
| CI | pytest; Windows and Ubuntu matrix; pinned GitHub Actions | No deployment, secret-bearing PR jobs, or personal self-hosted runner |
| UI | None required for the first slice | Add a small read-only dashboard after end-to-end agent interoperability, not before |

No Kubernetes, Kafka, Celery, vector database, blockchain, token marketplace, or distributed model inference is required at launch. A single trusted coordinating service plus independently owned agent hosts is enough to test the idea.

## Domain model

A contributor root is an admission record; one root can own several keys. A grant limits the root's contribution. A job freezes context and policy hashes. An assignment is a short lease with an unguessable nonce, a fixed maximum lifetime, and a persisted exposure record. A result is an immutable signed artifact reference. Reviews are typed evidence about that exact result. A promotion decision follows a fixed policy and machine-check receipts.

In the reference core the graph is deliberately shallow: producer result -> review jobs. General claims, dependency edges, failed approaches, reproducibility bundles, and proposal lineage are a later research-DAG layer, not implemented here.

## Trust and decentralization

V0 trusts the coordinator to admit roots, assign jobs, store history, and operate the deterministic checker. Execution can be decentralized without pretending the control plane already is. Cryptographic signatures detect artifact attribution/tampering; they do not prove real-world independence, model identity, honest scheduling, or mathematical correctness.

The private event hash chain detects accidental edits when its checkpoint is trusted. The operator can rewrite an unwitnessed chain; do not market it as immutable public transparency. Later independent witnesses may sign privacy-filtered checkpoint digests. Federation should follow a stable protocol and adversarial evaluation, rather than complicate the bootstrap.

## Deployment boundary

Production requires real OAuth/OIDC, ingress/TLS and rate limits, PostgreSQL concurrency tests, private backups, isolated workers, verified dependency locks, consent records, abuse response, and provider-integration review. The local CLI intentionally has no public bind option. Current absence of a deployment path is a guardrail, not proof that all hosting configurations are safe.

See [research sources](research.md), [threat model](threat-model.md), and [production persistence](postgres.md).
