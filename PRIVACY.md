# Privacy by default

DAIA should be public-ready without exposing a maintainer's personal identity, contact details, employer, clients, locations, home infrastructure, provider accounts, or private conversations.

## Repository policy

Use a public pseudonym and a GitHub noreply address for both author and committer. Do not copy private planning conversations or account profiles into documentation. Use reserved example domains and synthetic fixtures. Keep local databases, keys, tokens, logs, private configuration, signing material and diagnostics out of Git. `.gitignore` is not a secret scanner and does not remove old history.

The source includes a lightweight privacy guard for tracked files and commit metadata. It is a tripwire, not a guarantee of anonymization. Full-history, release, issue, screenshot, build-artifact and external-profile review is still necessary. Public aliases, repository ownership, timestamps and writing can be linkable; this project does not promise anonymity.

## Runtime policy

Store random contributor IDs and public keys rather than real names where possible. Keep private owner-linkage separate from any future public artifact feed. Development tokens are high-entropy bearer secrets stored by digest; never log or export them. Submitted artifacts and reviews can contain sensitive text, so even a signed artifact is not automatically public.

The bootstrap records minimal private events and aggregate counts and disables request access logs in its CLI. It does not include analytics, advertising SDKs or a public contribution graph. An infrastructure operator could still capture traffic/logs outside the application; review proxies and hosting defaults.

Only approved public or explicitly shareable project context should reach volunteer hosts. A donor's model provider may process that context under its own terms. Do not distribute personal, confidential, regulated or client data as volunteer work in this pilot.

## Retention and access

The local development database stays private on the operator machine until the operator deletes it. Production retention/deletion, backup expiry, scoped access, incident response, and contributor data export are not implemented. Set explicit retention and deletion rules before public launch, especially for artifact text, identity linkage, network metadata and troubleshooting traces.

Public cryptographic identifiers are persistent and can reveal relationships. Prefer per-project scoped identities or privacy-filtered exports after threat review; publishing full provenance may conflict with contributor privacy. Never put personal data on an irrevocable public ledger simply because a signature can authenticate it.

See [PUBLISHING.md](PUBLISHING.md) for the separate maintainer-publication checklist.
