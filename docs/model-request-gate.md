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

## Protocol and capability enumeration

Thirteen additional socket tests cover OPTIONS, model listing, OAuth discovery,
MCP/OpenAPI/tool paths, and JSON-RPC initialize, tools/list, resources/list,
prompts/list, rpc.discover and unknown methods sent to the model channel. Each
returns the same empty 403 and never invokes the upstream callback. The combined
suite now has 69 passing cases. This is local socket evidence, not yet guest-side
or real ChatGPT account capability enumeration.

This channel is model-only. The separate assignment MCP channel must legitimately
support its documented discovery protocol and expose only assigned heartbeat/result
operations. Hiding discovery is not the authorization boundary: operations must
remain denied even when an attacker already knows every method and endpoint name.
A complete worker-visible inventory must include all network routes, MCP servers,
provider-side tools and account functions; that inventory remains outstanding.

## Live enumeration with external credential injection

A fresh KVM guest performed all 23 hostile and enumeration probes against the
external channel, then the pinned original Codex executed the shell-canary task.
External counts: 23 denied, two forwarded. A distinct synthetic provider process
verified the injected bearer credential on both received requests. The credential
was generated outside the VM and not placed in its seed or environment. The provider
used a separate Unix socket, not a guest-forwarded network endpoint.

Native exit was zero, the tool and turn completed, and the overlay was removed.
Runtime: 47.349 seconds. This combines live guest-side enumeration, filtering,
local credential injection and positive native tool execution. The earlier ten-case
combined run also passed. Local 69-case suite passes with socket permissions; a
rerun without those permissions failed at socket setup, not protocol assertions.

The provider is a separate process under the same restricted external service
identity, not an internet provider or a separately attested trust domain. No real
OAuth credential, ChatGPT account function, refresh or revocation endpoint was used.
Exhaustion and active revocation remain unit/socket evidence until added to this
same guest trial. No exhaustive credential-extraction or sandbox-escape claim is
made from the absence of credentials in the prepared guest input.


## Live budget exhaustion after native tool completion

The next fresh KVM run completed 23 hostile/enumeration probes and the original
Codex shell-canary task, then sent one otherwise-valid extra model request.
The outside channel recorded three adapter attempts but only two forwarded calls;
the distinct synthetic provider authenticated exactly two requests. Total denials
were 24, including the exhausted-budget request. This establishes that the extra
request passed request validation and was stopped before the provider by the budget.

Native exit was zero; tool and turn completed; the overlay was removed. Runtime:
47.277 seconds. This remains synthetic-provider evidence. Active revocation and
real subscription lifecycle have not yet been demonstrated in the same KVM run.

## Original-client logout against a synthetic authority

`python3 scripts/probe_codex_logout.py /path/to/pinned/codex` runs the original
0.153.4 binary with a fresh temporary HOME and synthetic auth only. It pins the
binary digest, directs revocation to a loopback fixture, and checks both HTTP 200
and HTTP 503 replies. Neither case loads an existing user profile or credential.

Both cases passed: the client requested `/oauth/revoke` with the synthetic refresh
token and `refresh_token` hint, removed local auth, and exited zero. Therefore a
successful logout command is not proof of successful provider-side revocation.
DAIA must terminate its local assignment capability independently of that request.
This is a native-client local integration test, not real provider revocation,
login, refresh, hostile-guest isolation or a complete subscription lifecycle test.

Source: pinned official [revocation implementation](https://github.com/openai/codex/blob/3d2ee51ca2d5db578f328aa75e20aa22c0197c9a/codex-rs/login/src/auth/revoke.rs)
and [auth manager](https://github.com/openai/codex/blob/3d2ee51ca2d5db578f328aa75e20aa22c0197c9a/codex-rs/login/src/auth/manager.rs).
The same manager supports proactive refresh and a test endpoint override; testing
native refresh with synthetic credentials is the next lifecycle step.


## Native refresh and process restart with synthetic credentials

`python3 scripts/probe_codex_refresh.py /path/to/pinned/codex` runs the hash-pinned
original client twice with a fresh temporary profile and an expired synthetic JWT.
A local authority rotates both tokens. The first native model request carries the
new access token; a second, newly started Codex process loads the persisted tokens
and completes another model turn without requesting another refresh. Both processes
exit zero and return the fixture marker. Observed sequence: one refresh, then two
model requests authenticated with the refreshed token. Both rotated tokens persist.

The profile uses a custom Responses provider with `requires_openai_auth = true` and
the pinned client's refresh-endpoint override. No existing profile or real token is
loaded. These are native-client integration results against local HTTP fixtures,
not official-provider compatibility, production TLS, device login or a hostile-VM
credential boundary. Credentials intentionally reside in this trusted test profile;
this must not be copied into the worker. Native renewal across processes is now
established locally; connecting that lifecycle to the outside-worker credential
binding remains required before any real subscription test.


## Native refresh without trusted-side model execution

The same probe now accepts `--account-only`. It starts the pinned original
`codex app-server` over private stdio, initializes the connection and sends
`account/read` with `refreshToken: false`. An expired synthetic access token still
triggers native proactive refresh. After the process exits, a fresh process reads
the persisted account without another refresh. Both exits were zero, both returned
a ChatGPT account, and the fixture observed exactly one refresh and **no model
requests**. Both replacement tokens were saved. The model-mode probe separately
checks actual fixture answer markers; account mode checks account responses instead.

This removes the need to start a model task on the trusted controller just to
exercise renewal. It does not expose app-server to the worker: the native server
has broader account, process and thread operations and must remain private to the
trusted controller. No generic RPC relay is appropriate here. A bounded request
channel to the worker and a provider credential binding are still separate needs.

Source: pinned official [app-server account documentation](https://github.com/openai/codex/blob/3d2ee51ca2d5db578f328aa75e20aa22c0197c9a/codex-rs/app-server/README.md).
The native network-proxy [OpenAI credential provider](https://github.com/openai/codex/blob/3d2ee51ca2d5db578f328aa75e20aa22c0197c9a/codex-rs/network-proxy/src/credential_broker/providers/openai.rs)
handles `OPENAI_API_KEY`; it is not evidence of built-in ChatGPT OAuth brokerage.
