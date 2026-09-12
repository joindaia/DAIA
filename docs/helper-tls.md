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
