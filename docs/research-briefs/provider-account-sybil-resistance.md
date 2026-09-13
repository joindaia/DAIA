# Private provider-account binding as a Sybil-resistance signal

Status: research returned; production integration deferred. No admission or voting change.

See the [English assessment and actionable backlog](../research/provider-account-binding-assessment-2026-09-13.md) and its linked original report.
Date: 2026-09-13.

## Direction

Explore whether a participant can prove control of a Codex/ChatGPT or Claude
account while DAIA stores only a project-specific pseudonym. Multiple workers
linked to the same verified provider account would share an admission/review
identity rather than acquire extra voting weight merely by registering again.

A paid subscription may raise the cost of acquiring more identities. This is an
economic hypothesis, not proof of unique people, honest ownership, independent
reviews or current payment. One person can own several accounts; one organization
can own many seats. Local-model contributors must remain a supported category.
An account signal must not replace objective verification or execution limits.

A candidate identifier is HMAC(secret, unambiguous(provider, issuer, account-ID)).
The identifier must be stable across token refresh, scoped to DAIA, and kept out
of public jobs and GitHub. Do not hash access tokens or use plain email hashes.
HMAC is pseudonymization, not anonymity: the service can link contributions, and
key compromise or an exposed lookup service changes the privacy properties.

The unresolved prerequisite is trustworthy verification. A participant-controlled
helper can invent an account ID or a hash. Local authentication success and a
worker assertion do not establish a coordinator-verifiable identity. Do not send
provider credentials to the coordinator to solve this problem. No registration,
reputation or consent behavior changes under this proposal.

## Pro research assignment

Determine whether DAIA can verify provider-account control and deduplicate workers
without collecting provider passwords, access/refresh tokens, email addresses or
personal account data. Use current primary documentation and pinned client source.
Separate documented guarantees, inference, prototypes and live evidence.

Investigate Codex/ChatGPT and Claude separately:

1. Is there a supported identity-only authorization or attestation flow? Which
   stable subject identifies an individual account, organization, workspace or
   subscription seat? Are its issuer, audience, signature and intended use
   independently verifiable? Do not assume a client-readable claim is attestation.
2. Can proof be bound to a DAIA challenge, participant key and intended service,
   with replay protection, without DAIA obtaining inference or account authority?
   Compare provider-signed proofs, a narrowly trusted verifier, local attestation
   and voluntary declarations. State when none is feasible.
3. Design the smallest pseudonym scheme: domain separation, canonical encoding,
   verifier/key ownership, key rotation, account relinking, deletion, retention,
   erasure versus re-registration abuse, and protection against an enumeration
   oracle. State what each party learns and whether deployments can correlate IDs.
4. Distinguish account control from current subscription, payment, unique person
   and independent reviewer. Analyze multiple subscriptions, stolen/rented/shared
   accounts, free trials, enterprise seats and one person using both providers.
   Avoid covert cross-provider identity matching.
5. Quantify plausible attack costs only with sourced assumptions. What policies
   could reduce trivial duplicate voting without letting wealthy attackers buy
   authority or excluding local-model participants? Keep production, review,
   reputation and privileged execution separate.
6. Check provider terms and privacy obligations for the proposed identity use.
   Identify necessary consent and any provider confirmation, without claiming
   that ordinary CLI login automatically authorizes a new identity product.
7. Supply a minimal credential-free test harness and acceptance plan: fabricated
   claims, foreign issuer/audience, replay, swapped participant key, forged helper,
   expired proof, rotation, multiple workers per account, independent accounts,
   shared enterprise workspace, account removal and recovery.

Return a feasibility verdict per provider, a data-flow diagram, privacy/threat
analysis, concrete supported integration points and missing evidence. Recommend
against implementation if only participant assertions or collection of broad
provider credentials make the scheme possible. Do not contact providers, register
accounts, spend money or use personal credentials for this research.

Repository: https://github.com/joindaia/DAIA

## Initial decision boundary

Treat verified account binding, if feasible, as one abuse-resistance signal.
Same-account workers must not count as independent reviewers merely because
there are several worker keys. Different accounts do not prove independence.
No amount of account reputation or voting grants a worker unrestricted secrets,
network reach, repository writes or deployment authority.
