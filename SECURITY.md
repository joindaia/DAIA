# Security

This is a local reference implementation, not production-ready internet-facing software. It must not be exposed publicly with the development bearer-token verifier, unreviewed dependencies, or an untested MCP integration.

Do not publish secrets or exploit details in public issues. Use the repository's private vulnerability-reporting feature **after a maintainer has enabled and verified it**. No personal email address is published here, and the feature is not assumed to be enabled. Until a private channel is configured, do not open a public issue containing confidential evidence.

Agent-generated code and proof artifacts are untrusted. The coordinator must never execute arbitrary submitted commands or candidate-controlled evaluation code. Production runners must be isolated from operator credentials, deployment authority, donor tokens, host files and other projects.

All merges are human-controlled in the initial project. Authentication, permission mapping, signing, admission, assignment, verification policies, evaluator code, workflows, sandboxing and release authorization require protected review. Contributor agents cannot modify the rules governing their own acceptance.

See `docs/threat-model.md`, `docs/roadmap.md` and `docs/validation.md` for the current scope and unverified areas.
