# Research brief: personal subscriptions in isolated workers

Requested 13 September 2026. The [received research record](../research/personal-subscription-worker-auth-2026-09-13.md)
contains findings and their verification limits.

Determine whether DAIA participants can safely use their own ChatGPT/Codex or Claude
subscriptions for delegated jobs with the original, unmodified clients inside disposable
VMs. Local models and paid APIs are alternatives, not substitutes for this question.

The starting evidence is native Codex in KVM with an external assignment-bound helper,
including lost confirmations and exact retries, against simulated model responses.
Real subscription use has not been established by that evidence.

Use current primary sources to answer:

1. Which supported native and Docker credential-proxy login routes work in disposable
   VMs? Separate documented support from executed integration tests.
2. Where are credentials held, and what can malicious guest code do even without
   reading the actual token?
3. Can externally enforced authority limit the worker to inference, excluding personal
   chats, files, connectors, account management and other sessions?
4. How do login, refresh, restart, logout and revocation work? Which steps need the
   participant to act?
5. What do current terms permit for voluntary open-source contributions and paid jobs,
   without account sharing, pooling or a subscription-to-API translation service?
6. What is the smallest executable Linux/KVM proof, followed by Windows, with concrete
   configuration and positive and negative acceptance tests?

Assume arbitrary hostile execution in the guest. Host files, browser profiles, SSH
keys and private networks must remain inaccessible while useful public research,
code changes and tests remain possible. Give each provider a supported, limited or
unproven verdict and identify missing evidence and any explicit concessions.

Repository: https://github.com/joindaia/DAIA
