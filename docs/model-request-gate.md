# Experimental model request gate

`daia.model_request.RequestGate` is a pure validator, not a credential proxy or
production account-isolation boundary. Run it outside the guest before attaching
credentials. Its initial route is the synthetic `/v1/responses` laboratory route.

A trusted controller supplies an independently approved JSON template. Never learn
that approval from the first guest request. All non-history fields remain frozen;
local function tools and function namespaces are allowed, provider-executed tools
are not. Only explicit text messages, local function calls and text outputs are
accepted in history. Remote files, item references, previous-response links, opaque
reasoning input, duplicate keys, nonfinite numbers and unknown fields are denied.
The returned JSON is canonicalized; a caller must forward those returned bytes.

This establishes parser behavior only. HTTP framing/headers, routing, TLS, credential
injection, limits, revocation and service isolation are not implemented here. History
is untrusted candidate text, not proof of tool execution. Trusted local tool dispatch
and evaluation remain separate obligations.

Compatibility ceiling: images, encrypted reasoning, WebSockets and compaction are not
yet supported. These may be necessary for useful real Codex work. Do not call the
subscription objective complete by disabling useful behavior to fit this validator.
Public research must remain available through the separate bounded guest research
route. The next test is integration with the pinned native client, followed by adding
necessary representations only when their authority and ownership can be checked.

Validation: 25 local tests cover multi-turn text/function history, assignment
namespaces, native MCP text outputs and negative authority/parser cases. These tests
do not establish real provider authentication, provider-side scope or VM integration.

## Native-request replay, 13 September 2026

A new KVM run captured five complete requests from the pinned original client,
using synthetic model answers and the real assignment helper. The run completed
with one coordinator result, exact retry and successful host-canary controls.
The bodies remained private; no provider credentials were present.

Initial replay failed: the client requests `reasoning.encrypted_content` in its
output inclusion list, and inline history items carry IDs. The gate now permits
that frozen output option and removes optional IDs from complete inline items.
It still rejects item references and encrypted reasoning *input*. Provider behavior
with removed IDs, and real reasoning continuity, still require integration evidence.

All five captured requests now pass an offline replay outside the guest. The replay
used the recorded first request as a compatibility template, NOT as a production
approval mechanism. A real controller must independently approve its template.
This is not inline filtering of live VM traffic and not external secret injection.

31 unit cases pass. Independent review found that earlier malformed-JSON tests
could pass for unrelated profile mismatches. New otherwise-valid duplicate-key
requests and nonfinite template cases now target those parser protections directly.

## Bounded transport prototype

`daia.model_channel.serve_once` connects the validator to a single-request HTTP/1.1
socket handler. Only the fixed laboratory route and authority are accepted. Duplicate
headers, alternate routing, guest authentication, transfer/content encodings and
upgrades are refused before invoking the trusted callback. Only canonical validated
JSON reaches that callback; no guest header is forwarded.

46 combined unit/real-socket tests pass. The socket tests run in threads in one test
process, with a synthetic credential owned by the callback. They establish forwarding
order and absence of that synthetic secret from the fixture response, **not** process
or VM credential isolation, external network denial, TLS or provider compatibility.

The prototype buffers a response up to 8 MiB rather than forwarding live SSE. A
separate watchdog must bound total service/callback time. Provider errors, arbitrary
response content and headers need independent handling before credentials can be
used. Native client headers, compression and useful long-running streamed responses
must be covered during integration; the strict laboratory header set is not yet a
verified native production profile. No listener is installed by this module.

## Native transport observation and review

The original Codex binary completed a fresh KVM shell-tool fixture against the
external synthetic server (46.917 seconds; zero native exit; temporary overlay
removed). This run observed `application/json`, no content encoding and no
Authorization header. In addition to standard HTTP fields, it sent `originator`,
`session-id`, `thread-id`, `x-client-request-id`, `x-codex-beta-features`,
`x-codex-turn-metadata` and `x-codex-window-id`.

The channel accepts these metadata header names but discards their values; it
never forwards guest headers to the trusted callback. The trusted launcher may set
an exact expected Host value for its fixed virtual endpoint. That value is not a
forwarding destination. The native observation still used the existing fixture
server, not this new channel: full inline integration remains outstanding.

Independent review identified possible double responses after a partial success
write. The handler now closes on that failure rather than appending a 403 inside
an unfinished SSE response. Partial-write, pipelining, model-binding and native
metadata tests bring the combined total to 50 passing cases.

## Live external-channel KVM trial

The pinned native Codex client completed a shell-tool task through `serve_once`
and `RequestGate` running in the separate non-root gateway service outside KVM.
The trusted callback supplied synthetic Responses events. Two validated requests
reached it, the actual guest shell created/read the expected canary, Codex exited
zero and completed its turn, and the disposable overlay was removed. Runtime was
47.232 seconds. Staged external server SHA-256:
`836cdc367836047f9d077d723d65649d63dceb16b5a1734e768724bb99faeaeb`.

The lab prepared a frozen template from a separate controlled native run, not from
an unknown incoming job. The lab wrapper removed `client_metadata` and
`prompt_cache_key` before template comparison and forwarding. Those tracing fields
vary between sessions; removing them has only been tested against the synthetic
provider, not ChatGPT. The repository validator itself was not weakened to learn
or accept arbitrary guest profiles.

This establishes live native tool-use compatibility through the external channel.
It does not establish hostile-request rejection from inside KVM (socket tests cover
those cases locally), secret injection to a distinct upstream service, account
confinement, real inference, public research, independent patch evaluation or
subscription lifecycle. The fixture's external-only synthetic marker was not a
provider credential; no credential-isolation claim follows from generating it.
The combined assignment-helper retry test remains a separate earlier run.

## Hostile guest followed by useful tool execution

A fresh KVM guest sent ten hostile HTTP requests before starting the original
Codex client. The external service counted ten denials and exactly two forwarded
requests. Codex then successfully executed the shell canary and completed its turn;
the overlay was removed. Runtime: 47.749 seconds. Staged external server SHA-256:
`f8b51e2fd6e38d133ed31dd56b3568d75e8122378d961ee8082e24c36a6961b6`.

Rejected cases: guest Authorization, Transfer-Encoding, duplicate Content-Length,
WebSocket upgrade, connector path, CONNECT tunnel, replacement hosted MCP tool,
foreign previous-response reference, item reference and enabling stored responses.
Both the guest's explicit 403 checks and the external adapter counters agreed.
The external service remained usable for the positive task after those attacks.

These attacks exercised the live VM-to-channel path, not provider account actions.
The template and tracing normalization are the same controlled lab concessions as
above. Real credential injection, provider scope enforcement, independent patch
evaluation and subscription lifecycle remain untested. Do not infer protection
against every HTTP attack or sandbox escape from these ten bounded cases.

## Local credential adapter prototype

`LocalModelUpstream` sends canonical gate output to one controller-selected Unix
socket and fixed `/v1/responses` path. It supplies its own synthetic bearer header;
worker headers and destination selectors are absent. Only one call may be active.
Attempts consume a finite request budget. Expiration rejects new calls and late
responses; revocation shuts down an active socket and rejects future calls.
The send phase is serialized with revocation and has a bounded socket timeout.

56 combined tests pass. Six new cases exercise a real local HTTP provider socket:
fixed credential/path, exhausted budget, redirects, error responses, literal secret
reflection, interrupted in-flight response and expiration before connection (some
properties share a case). All are synthetic and run inside the test process; this
is not evidence of OS-level credential separation or live KVM credential isolation.

No TLS/internet/provider-account integration is implemented. The provider response
is buffered, requires one bounded Content-Length and cannot be compressed/chunked.
Literal-secret reflection is rejected, but encoded/transformed exfiltration is not
covered: this is not a general response data-loss prevention mechanism. A trusted
provider route, response contract and process boundary remain required. A separate
watchdog is still necessary to enforce total execution time against slow traffic.
