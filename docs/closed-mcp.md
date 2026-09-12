# Closed MCP admission

The owner authorized preparation of a public HTTPS MCP endpoint with registration
closed and only pre-admitted agents allowed. This first implementation adds the
admission gate; it does not authorize or implement direct Internet exposure of the
development adapter. Existing public-launch gates still apply.

## Operator configuration

Start `serve-mcp` with `--allowed-agents /operator/private/allowed-agents.json`.
The file is a JSON array of exact registered agent IDs (64 lowercase hexadecimal
characters). Keep real IDs in private operator configuration, not this repository.
The file supports at most 256 unique IDs and 20,000 bytes. An empty array denies all
agent work. Missing, malformed or oversized files fail startup with a fixed error.
The process takes an immutable snapshot: changes require a deliberate restart.

When supplied, registration_challenge and register_agent are not registered as MCP
tools. The six remaining work tools check allowlist membership before invoking the
coordinator. Existing owner binding, revoked key/root checks, finite grant expiry,
lease fencing and signatures still apply. Listing an unknown agent does not register
it. Adding an ID does not grant budget or extend consent. Admission is operator-only.

When the option is absent, the existing private pilot's behavior is unchanged. A
future public launcher must require this file explicitly and refuse to fall back to
open registration. Removing an ID also blocks its receipt recovery and lease calls;
drain or reconcile outstanding work before removal when possible. Urgent revocation
can deliberately stop access; no deadline or history is reset.

## Boundaries still to build and verify

An ID is an admission label, not proof of possession on every operation. Current
work/status calls authenticate the contributor token; signatures protect registration
and result submission. Do not describe the list as an independent identity factor.
Public transport needs a separately reviewed authenticated entry point, strict
canonical resource/host/origin handling, pre-auth request and connection limits,
slow-client deadlines, bounded storage and a tested client migration. No public bind,
DNS change or reverse proxy is introduced by this increment. No personal-tailnet
access or arbitrary contributed execution is enabled.

The current MCP profile uses development bearer grants and is not a complete OAuth
resource-server deployment. A closed machine cohort may use a reviewed mutual-TLS
gateway as an additional gate, but desktop/client support and revocation must be
proved before selecting it. Broad native-host compatibility requires standard MCP
authorization integration. This document does not claim either path is implemented.

## Validation of this increment

Full Linux suite: 229 passed, two Windows-specific skips, one existing dependency
warning. Real SDK/HTTP tests exercise absent registration tools, all six denied work
tools, same-owner excluded keys, different-owner access denial, empty-list deny-all,
immutable policy snapshots and successful signed submission/replay for an admitted
agent. Additional closed-mode tests reject unregistered and revoked agents, and
expired or revoked contributor grants. File tests cover malformed/duplicate/oversized input; subprocess CLI tests
check missing/invalid policy refuses service startup without exposing its path.
CI and public deployment are separate checks.
