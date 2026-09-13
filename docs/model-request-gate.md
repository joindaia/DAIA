# Experimental model request gate

`daia.model_request.RequestGate` is a pure validator, not a credential proxy or
production account-isolation boundary. Run it outside the guest before attaching
credentials. Its initial route is the synthetic `/v1/responses` laboratory route.

A trusted controller supplies an independently approved JSON template. Never learn
that approval from the first guest request. All non-history fields remain frozen;
local function tools and function namespaces are allowed, provider-executed tools
are not. Only explicit text messages, local function calls and text outputs are
accepted in history. Remote files, item references, previous-response links, opaque
reasoning state, duplicate keys, nonfinite numbers and unknown fields are denied.
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
