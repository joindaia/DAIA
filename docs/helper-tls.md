# Contributor client certificates

The local helper can optionally load a client certificate for mutual TLS. This is
transport groundwork for the closed cohort, not a deployed public gateway. Current
endpoint restrictions remain: loopback or the configured private-tailnet form. No
public domain is enabled by this change.

An operator-provided invite may include `tls` with exactly three nonempty path
strings: `ca_file`, `certificate`, and `private_key`. Relative paths resolve beside
the invite. These files stay in private local storage, outside job artifacts and
source control. Certificate files and key permissions must protect the helper's
identity from other users and contributed code. This feature does not isolate the
parent agent's filesystem access.

The helper verifies the server's certificate and hostname against the supplied CA,
requires TLS 1.2 or later, and presents its own certificate. TLS configuration is
rejected on HTTP. Missing or invalid credentials fail before writing contributor
state, with a fixed diagnostic; encrypted keys are not prompted for interactively.
Invites without TLS configuration keep existing behavior. Existing identity,
consent, stop state, receipts and budget are unchanged. An endpoint migration still
needs an explicit state migration; editing the URL of an existing invite is refused.

A real loopback HTTPS MCP test uses temporary certificates and requires the client
certificate at the server. The helper retrieves status successfully, while missing
client credentials or an untrusted server fail. No real agent credentials, public
endpoint, certificate issuance process, revocation service or VPS deployment is
created by these tests.

Before public cutover, implement the mandatory closed launcher and gateway limits,
certificate-to-agent binding and revocation, verify the reverse proxy cannot bypass
that binding, and test migration/recovery with existing helper identities. Direct
native MCP clients without certificate support need a separate authorization path.

## Explicit endpoint migration

The operator can prepare a JSON document with exactly `url` and `tls` (the three
credential paths above), then run:

```sh
python -m daia.contributor --invite /private/invite.json --migrate-endpoint /private/endpoint.json
```

This is a one-shot CLI operation, not an agent-callable MCP tool. Stop the helper
before using it; the existing invite lock prevents simultaneous local hosts. The
public destination must be a canonical HTTPS `/mcp` URL with a DNS hostname and
client TLS credentials. Relative credential paths resolve beside the endpoint
file; the saved override uses absolute paths.

Both coordinators must support migration checks. After the operator has paused
claims and restored a verified snapshot, the helper compares authenticated network,
root and agent identity, grant, lease and the contributor's durable history digest
on source, destination and source again. Differences or connection failures refuse
migration. This is a consistency check against trusted endpoints, not a proof that
a server is honest or an atomic distributed cutover. The operator must prevent
writes between snapshot verification and cutover and independently verify the full
database restore. Other contributors' history is not returned by this check. The contributor root
is the confidentiality boundary: registered sibling agents under that root can
observe that the root-wide digest changed, just as they share the grant allowance.
The digest is opt-in on `contribution_status`; ordinary helper polling omits it.

Only the saved transport changes, using the helper's atomic state replacement.
The original invite, key, local usage, deadline, stop flag, lease and pending result
remain intact. A private pre-change state backup is written beside the state file;
on Windows, the enclosing directory's ACL must also protect it. Do not feed these
files to worker jobs.

```sh
python -m daia.contributor --invite /private/invite.json --switch-back-endpoint
```

Switchback verifies both endpoints again and selects the previous transport. It does
not restore old usage or results from the backup. A stale or unreachable endpoint
therefore requires operator recovery rather than silently losing intervening work.
Neither action extends consent. Ordinary reconnects use the saved transport override.

Unit tests cover preservation, mismatch, unreachable destination and failed save.
A real SDK HTTP-to-mutual-TLS test exercises migration, restart and rollback using
an ephemeral loopback routing exception in the test only. Public-host routing,
closed-gateway integration and populated off-host recovery still need combined
acceptance before live cutover.
