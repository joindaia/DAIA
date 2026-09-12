# Closed cohort gateway: implementation contract

This is the next implementation slice after closed MCP admission and helper client
TLS support. It is not an installed gateway or permission to expose the development
adapter. The first cohort uses the local stdio helper, which presents its client
certificate; direct native desktop HTTP clients are outside this first release.

## Request path and authority

A dedicated HTTPS hostname terminates mutual TLS at the gateway. A private DAIA
client CA signs cohort certificates. Keep its signing key off the coordinator and
outside worker access. Server TLS uses a separately managed server certificate.
An unrecognized, expired or revoked client certificate must fail before MCP routing.

Use a private Unix socket between gateway and coordinator, readable only by the
service accounts. Do not expose an alternate TCP listener that bypasses the gateway.
The public launcher must require a nonempty explicit deployment policy; its agent
list may be empty to suspend all work. It must not fall back to the private pilot
profile or expose the REST operator adapter against the production database.

Bind each accepted client certificate to one registered agent using operator-owned
configuration. The gateway must overwrite, never forward, caller-supplied identity
headers. The coordinator must check this authenticated agent identity on every
agent-bearing tool call, including receipt recovery. Keep the original contributor
bearer/grant checks and agent-to-root ownership checks. A valid certificate cannot
choose another admitted agent, enlarge its budget or perform registration.
Initialization and session reuse must remain bound to both contributor and certificate
identity; a reused MCP session cannot cross that boundary.

A certificate is a transport credential, not independent personhood or reputation.
Do not issue a certificate based on a job result, vote or model-written instruction.
Certificate renewal and revocation are maintainer operations; neither renews consent.

## Routing and resource limits

Accept the configured host and exact MCP route only, with the required MCP methods.
Reject unexpected Host/Origin values and ambiguous paths. Do not accept arbitrary
forwarded host, scheme or identity headers. Keep redirects away from authenticated
MCP traffic. The server's advertised resource must match the public HTTPS endpoint.

Enforce the existing 16 KiB body ceiling before upstream forwarding, bounded request
headers, connection and request-rate caps, and header/body idle deadlines. Set a finite
upstream timeout that accommodates the helper's current 30-second operation deadline.
Avoid response buffering that breaks streamable HTTP. Return bounded errors without
credentials, request bodies, internal paths or certificate details. Initial numeric
connection/rate limits are operator settings to validate under a bounded load test,
not a claimed capacity benchmark.

## Required executable acceptance tests

- Real helper registration is prepared privately; public registration tools are absent.
- Registered, admitted, certificate-bound helper can inspect status, claim, heartbeat,
  submit a signed result and recover the identical receipt after reconnect.
- Missing/untrusted/expired/revoked client certificate is refused before tool execution.
- Correct client certificate with a wrong server name or CA fails locally.
- Valid certificate with a different agent ID, another root token, or another session
  cannot obtain or mutate that identity's work.
- Spoofed identity/forwarding headers do not change the bound agent or resource.
- Invalid deployment policy refuses startup; no REST or direct TCP bypass is reachable.
- Oversized, slow and excessive requests are bounded without breaking normal MCP calls.
- Restart and certificate rotation preserve database history, pending receipts, stop
  state, consumed allowance and the original absolute consent deadline.

Run these on disposable staging state first. Then restore a checked pilot snapshot
offline, verify reconciliation, and prepare each existing helper's explicit endpoint
migration. Pause claims and drain/recover outstanding work before the cutover. Preserve
a tested rollback path and never run both coordinators against diverging writable
copies. No worker-provided executable artifacts run on either service host.

## Review requirements before implementation

The first review identified the following integration gaps. Existing helper and
server endpoint restrictions are intentional; they cannot be bypassed by editing
an invite or advertising a public hostname as a tailnet endpoint.

1. Add a separate canonical HTTPS resource configuration for the closed launcher.
   Add an explicit operator-approved helper migration that verifies the destination
   network and agent binding, backs up existing state and preserves key, root, stop
   state, pending receipts, usage and absolute consent expiry. Refuse plaintext,
   ambiguous endpoints and implicit identity resets. Changing a URL alone remains
   insufficient. Validate recovery and rollback before any live migration.
2. Map exact certificate fingerprints to registered agent IDs in operator-owned
   gateway policy. Establish a trusted identity context only from the private socket
   transport. Compare the bound ID against every agent-bearing tool call; an ID
   supplied by the caller is not certificate authentication. Missing, duplicate or
   malformed identity assertions fail closed. The public profile cannot reuse the
   private profile's optional identity checks.
3. Bind sessions to the authenticated pair of contributor root and certificate-bound
   agent. Test replay with the same root but another certificate-bound agent as well
   as another root. Define rotation behavior explicitly: a certificate for the same
   agent does not reset consent or history, and removal must affect existing sessions.
4. Use a dedicated socket parent directory owned by the coordinator service account,
   with a dedicated gateway-connect group and mode 0750; set the socket owner/group
   accordingly with mode 0660. Only the gateway account belongs to that group. The
   coordinator necessarily retains ownership and access to its socket; root remains
   a trusted administrator. Workers and unrelated service accounts get no traversal
   or connect access. Verify actual ownership, group membership and mode, not merely
   the template. Launch only with the Unix socket and verify that the deployment has
   no alternate coordinator TCP listener or REST service against the same database.
5. Add explicit valid-certificate cases with absent, expired and revoked bearer
   grants. Verify both registration tools are unavailable. After restart, endpoint
   migration and certificate rotation, test the original consent deadline boundary
   and exhausted/stopped state rather than checking only that saved fields match.

These are requirements for the next code change, not controls already supplied by
PR19. Certificate lifetime, revocation publication and gateway reload behavior need
an executable staging exercise before the public route is enabled.

## Implemented adapter increment

`build_mcp_app(..., allowed_agents=..., certificate_agents=...)` now supports an
opt-in certificate-bound adapter. The certificate policy maps lowercase SHA-256
fingerprints to registered agent IDs, takes an immutable startup snapshot, and requires
an explicit allowlist. The gateway must inject exactly one
`X-DAIA-Client-Cert-SHA256` header after verifying the client certificate. Requests
with an IP peer are refused; Unix-socket permissions remain an essential deployment
boundary. The adapter does not itself verify a TLS certificate or create that socket.

Bearer verification checks the bound agent's current root ownership, registration,
revocation and grant. The SDK authorization principal includes both root and bound
agent so sessions cannot cross those identities. Every agent-bearing tool checks its
argument against the authenticated agent, including same-root agents. This does not
turn the header into a trusted identity on a TCP listener.

Real Unix-socket tests cover a successful status call, same-root cross-agent tool
and session rejection, wrong-root rejection, expiry, hidden registration tools,
invalid/duplicate certificate headers and immutable policy. A separate real TCP test
rejects even a correctly formed identity header. Public URL configuration, launcher,
proxy, certificate lifecycle and helper migration are still unimplemented. The
private profile and existing live pilot remain unchanged.

## Closed backend launcher

The subsequent launcher increment is `python -m daia.gateway --config POLICY.json
--db EXISTING.sqlite3 --socket /run/daia-gateway/mcp.sock`. This starts only the
backend on a prebound Unix socket; it does not install or expose a TLS proxy.

The policy must be an integrity-protected regular file: symlinks, FIFOs and
group/world-writable POSIX files are refused before parsing; POSIX ownership must
belong to root or the service user. The policy must contain exactly `resource`, `allowed_agents` and `certificate_agents`.
The resource is a canonical lowercase `https://DNS-NAME/mcp` URL with implicit port
443 and no query, fragment or user information. Public resource mode requires both
certificate binding and closed admission; private tailnet mode cannot be combined
with it. Public mode accepts only that exact Host and HTTPS Origin, without loopback
aliases. There is no public bind or host/port fallback option in the launcher.

Prepare the socket directory as the nonroot service user with its dedicated gateway
connect group and mode 0750. The launcher requires matching effective UID/GID, rejects
symlinked paths and untrusted writable ancestors (root-owned sticky temporary parents
are permitted for isolated tests), and binds a new socket with mode 0660. It refuses
any existing path rather than unlinking another process's socket. Graceful shutdown removes only the exact socket inode created by this process, so
a normal restart can bind again. After an uncatchable crash, the operator must verify
the process is gone before removing a stale socket. Replaced paths are preserved.

The database must already exist; a misspelled path cannot create fresh coordinator
state. The gateway-to-backend hop is HTTP over the private socket, while the canonical
client-facing resource is HTTPS. Forwarded-header interpretation is disabled. The
proxy must replace Host with the configured canonical name and must replace the
certificate assertion after certificate verification. Group membership, proxy
configuration, revocation, ingress limits and real helper migration remain deployment
work. This launcher alone is not a secure public service.


### Launcher review validation

The review identified unsafe policy inputs and stale sockets after normal shutdown;
both are addressed with descriptor-based policy checks and identity-checked cleanup.
Regression tests verify the normal SIGTERM path, failed ASGI startup cleanup, and
preservation of a replacement pathname. Startup failure remains nonzero.
The suspected empty/unrelated database acceptance did not reproduce: the existing
Coordinator constructor already queries initialized network metadata before binding.
New subprocess tests confirm refusal without creating a socket. This is a startup
sentinel check, not a comprehensive database integrity or migration audit.

The follow-up lifecycle review also identified signal-delivery windows around binding
and cleanup. The socket context now blocks SIGTERM before binding and until a graceful
server handler is installed; shutdown blocks it again until the original captured
socket has been removed. Deferred signals are delivered only after cleanup. Tests
send actual SIGTERM in the pre-handler and cleanup windows, verify the resulting
termination leaves no socket, and verify cleanup after a working-directory change.
Only the captured absolute path and inode are used; replacement paths remain intact.
SIGKILL, kernel failure and power loss still require stale-socket recovery.

## Nginx certificate forwarding increment

The closed launcher now accepts `X-DAIA-Client-Cert` from its trusted Unix-socket
proxy. It parses one URL-encoded PEM certificate, bounded to 8192 encoded bytes,
derives the SHA-256 fingerprint, and discards every incoming fingerprint assertion
before passing the derived identity to the certificate-bound adapter. Missing,
malformed, oversized or duplicate certificate fields fail closed. This parser does
not validate a chain: Nginx must require and verify client certificates first.

Nginx's built-in fingerprint variable is SHA-1, so it must not populate the existing
SHA-256 policy field. The escaped certificate variable supplies the leaf certificate
instead ([official Nginx SSL variables](https://nginx.org/en/docs/http/ngx_http_ssl_module.html#variables)).
The lower-level adapter retains its fingerprint assertion interface for trusted
integrations; the closed launcher always performs the certificate translation.

`deploy/nginx-closed-mcp.conf.example` is an inactive HTTP-context template listening
only on loopback. It requires a client CA and CRL, disables TLS session resumption,
overwrites certificate/forwarding headers, restricts Host/path/methods and sets initial
body, idle-time, per-IP request and connection bounds. These numbers are starting
settings, not capacity claims. Public deployment, slow-client/load tests and helper migration remain unverified.
The isolated CRL reload checks are described below. No live Nginx config
is changed by adding this template.

### Full proxy integration exercise

`tests/test_nginx_gateway.py` runs real temporary Nginx and backend processes, synthetic
CA/client/server certificates, a disposable coordinator and a loopback port. It passed
on the VPS: an admitted client claimed work, submitted a signed result and recovered
the same receipt; spoofed forwarding headers were replaced, missing and unadmitted
client certificates were refused, and oversized bodies and unexpected query strings
were rejected. An updated CRL followed by proxy reload refused the revoked certificate
on new TLS connections. The stdio helper's endpoint migration remains untested by this exercise.

Linux CI installs Nginx and requires the integration test to run; environments without
Nginx skip it explicitly. The test does not start a public service or modify the VPS's
live configuration. Slow-client/concurrency stress and live helper migration remain separate acceptance
checks.

### Closing streams after certificate revocation

Use `deploy/nginx-gateway-main.conf.example` for a dedicated gateway Nginx instance,
with the HTTP site template included from it. Its main-context
`worker_shutdown_timeout 5s` bounds old worker shutdown after a successful reload.
Do not substitute this configuration for the existing website service. The gateway
account needs its own private writable runtime directory and socket access.

The regression test first reproduced an open authenticated SSE stream surviving a
CRL reload beyond eight seconds, although new TLS requests were already refused.
With the main template, the same real proxy test passed on disposable VPS state:
new requests were refused and the old stream closed within the eight-second test
bound. This is measured acceptance evidence, not an instantaneous revocation claim.

A reload drains all old worker connections, including admitted clients. They must
reconnect; previously stored results remain recoverable through the receipt protocol.
An interrupted operation may have committed before its connection closed. Do not
interpret disconnection as rollback or renew consent to retry it.

Revocation operations must validate configuration, confirm the reload was accepted,
and confirm both new-connection refusal and old-stream closure. Sending SIGHUP alone
is insufficient: a rejected reload leaves the old configuration active. This patch
adds the configuration and test, not a deployed revocation management service.
See [Nginx worker shutdown documentation](https://nginx.org/en/docs/ngx_core_module.html#worker_shutdown_timeout).

### Idle request clients

The real Nginx exercise also holds two authenticated TLS connections open: one
stops halfway through the HTTP headers, the other advertises a body and sends only
its first byte. Both must close within fourteen seconds, optionally returning HTTP 408 first, under
the template's ten-second header/body idle timeouts. A subsequent authenticated
MCP initialization must still succeed. The isolated VPS exercise passed in 17.79s,
including the existing submission, receipt replay and stream-revocation checks.
A negative control with sixty-second idle limits failed with a read timeout.

These checks cover clients that stop sending. They do not establish resistance to
continuous slow trickles, connection floods or a production capacity limit. Per-IP
concurrency and rate-limit acceptance remain separate work before public exposure.

### Concurrent active requests

The real proxy exercise opens twenty authenticated SSE streams from one loopback
IP, each in its own MCP session. Initialization, notification and GET requests are
paced below five requests per second. While those streams remain open, a further
initialization must receive HTTP 429. Closing the streams must allow initialization
again within three seconds. The isolated VPS exercise passed in 32.20s, including
the earlier receipt, idle-client and revocation checks. A negative control raising
only the connection limit to twenty-one failed because the extra request returned
HTTP 200 instead of 429.

This validates the configured per-IP limit for active requests, not twenty machines
or a measured service capacity. Participants sharing a public IP also share this
limit. Request-rate bursts, distributed floods, incomplete pre-header connections
and continuous slow uploads are not covered by this check.

### Request bursts

The same real proxy exercise sends eighty sequential authenticated initialization
requests over one client connection. Responses must be HTTP 200 or 429, at least
one request must be rate-limited, and the burst must finish within ten seconds.
After five seconds without new requests, initialization must succeed again. One
request is active at a time, keeping this check separate from concurrent streams.
The isolated VPS test passed in 37.64s with the configured five-requests-per-second
rate and twenty-request burst allowance. Removing only the request limiter made
the negative control fail because no request returned 429. The test does not
calibrate the exact rate or distinguish nearby rate/burst settings.

These bounded tests exercise configured rejection and recovery. They are not a
throughput benchmark or protection against distributed traffic. Slow continuous
uploads and pre-header connection pressure remain separate deployment concerns.
