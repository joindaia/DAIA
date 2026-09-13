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

## Rejected native refresh does not authenticate an account response

The refresh probe accepts `--account-only --reject-refresh`, optionally with
`--force-refresh`. The local authority returns HTTP 401 with the synthetic
`refresh_token_invalidated` code. Both variants completed two native processes
with zero exit codes and normal account RPC responses, but neither replacement
token was saved; the expired access token remained unchanged. Each observed run
made four refresh attempts and no model requests. Retry count is observed evidence,
not a promised client contract.

An exploratory automatic-refresh run returned an account on one process and no
account on another. The assertions deliberately do not require that incidental
metadata outcome. The pinned [account processor](https://github.com/openai/codex/blob/3d2ee51ca2d5db578f328aa75e20aa22c0197c9a/codex-rs/app-server/src/request_processors/account_processor.rs)
invokes refresh but does not propagate its outcome as an account/read RPC error.
Consequently a successful RPC or a remembered account cannot authorize a DAIA
model binding. The trusted side must establish usable credential state, including
freshness and expected account binding, and reject unavailable or failed renewal.
This check is a remaining integration requirement, not implemented by this probe.
The normal account-only refresh control still passes afterward.

## Native refresh connected to the local model binding

Run with `PYTHONPATH=src python3 scripts/probe_codex_refresh.py
/path/to/pinned/codex --account-only --binding`, and repeat with
`--reject-refresh`. The native private `getAuthStatus` request returns the
refreshed synthetic access token on success and no token after the fixture's
permanent refresh failure. This RPC remains entirely on the trusted side.

On success, the probe supplies that exact fixture-issued credential to
`LocalModelUpstream`, sends an unauthenticated request through `serve_once` and
`RequestGate`, and receives the synthetic model marker. The provider observes the
new bearer credential; the channel response does not contain it. A fresh native
process repeats the operation using persisted auth. Observed sequence: one refresh,
two authenticated model calls, two admitted bindings. On rejection: four observed
refresh attempts, no model calls and zero admitted bindings. Both runs exit zero.

The adapter now accepts bounded JWT-shaped credential strings containing dots;
whitespace, header injection, nonstrings and oversized values remain rejected.
All 75 gate/channel/adapter tests pass, including exact JWT-shaped header injection
and malformed credential rejection before connection.

This integration uses local sockets in a test process, not the hostile KVM path.
The probe's admission oracle requires the exact synthetic token issued by its
fixture. It is **not** a production validator for arbitrary credentials, token
freshness, account identity or provider authorization. No real subscription is
accessed, and no broader native account interface is exposed through the model
channel. Next: transfer the combined flow into the restricted external service
and fresh KVM trial, preserving the existing assignment deadline and request budget.


## Native renewal followed by live KVM model use

The combined lab now ran through a fresh KVM overlay. A separate restricted
nonroot auth service first ran the original app-server twice: one synthetic token
refresh, persisted replacement tokens, no model requests. This service used a
private network namespace with loopback for its synthetic authority. The gateway
retained its AF_UNIX-only configuration; the worker configuration was unchanged.
The verified synthetic token was handed to the gateway in a mode-0600 file outside
the guest and deleted when consumed. No native account RPC reached the worker.

The original guest Codex completed the shell-canary task through the gate and
credential adapter. The external provider authenticated two requests. All 23 guest
attacks were denied; a third valid adapter attempt exhausted the two-request budget
and did not reach the provider. Total external denials: 24. Runtime: 46.039 seconds.
The overlay, credential handoff file and gateway/provider sockets were absent after
cleanup. Structured [evidence](research/native-auth-kvm-evidence-2026-09-13.json)
records the binary/server digests and counters without raw credentials or profiles.

This reused the fixture seed with a fresh overlay; it is not a new DAIA assignment
or a new consent grant. Auth refresh completed before guest launch, so renewal
*during* a job is still untested. Separate native-auth, gateway and synthetic-provider
processes share the restricted external service identity. This is not a proof of
real ChatGPT account confinement, credential extraction resistance against every
route, TLS compatibility, real subscription inference or useful patch evaluation.
The negative native refresh/admission case remains the separate local probe.

## Credential replacement preserves assignment authority

`LocalModelUpstream.replace_credential` is a trusted-controller method, not a
worker endpoint. It accepts a replacement only between requests on an active
binding. It cannot reset the deadline or request budget, revive a revoked binding,
or change credentials during an in-flight response. The controller remains
responsible for credential provenance, freshness and account binding. Five added
tests exercise these properties and malformed replacement; 80 combined tests pass.
Literal response-secret checking remains limited to the current credential and is
not a general DLP guarantee, including for previous credentials or encoded secrets.

A fresh KVM-overlay run exercised replacement between the two native model calls.
The restricted auth service generated two distinct synthetic access tokens through
two original-client refreshes before guest launch. The provider required the first
token on its first request and the replacement on its second. The external adapter
replaced the credential after the first completed call, retaining its original
150-second/two-request allowance. Both requests succeeded; 23 hostile probes and
one extra valid request were denied. External counters: three adapter attempts,
two forwarded, 24 denied, two authenticated provider requests. Runtime: 46.077s.
Native tool/turn completion and overlay removal succeeded. Both one-use handoff
files and provider/gateway sockets were absent afterward. Server digest:
`1e5578d35923634af39f2fdff180e11925cca840ea5f69df8edf1a8e03eefdb6`.

The replacement tokens were prepared before guest execution. This proves switching
credentials during the two-call task without renewing authority, not real-time
refresh on expiry, reactive 401 recovery, real provider acceptance or a complete
subscription lifecycle. Refresh requests still need a controlled trusted-side
trigger and failure handling in the eventual runtime integration.


## Native renewal triggered during the running KVM task

A subsequent fresh-overlay trial kept the restricted auth service waiting after
its first successful native refresh. Only after the first completed model call did
the gateway signal renewal. The trusted lab then replaced the synthetic access
token in its own profile with an expired fixture JWT. The second original-client
process performed native proactive renewal and supplied a different token. The
existing gateway binding used it for the second request without resetting budget
or deadline. The provider required the first then replacement token in that order.

Runtime: 47.254 seconds. Both native auth processes exited zero; two refreshes and
two authenticated model requests were observed. The guest completed its tool and
turn. All 23 hostile probes and the extra valid over-budget request were denied;
external counters remained three adapter attempts, two forwarded, 24 denied.
The overlay, both token handoff files, renewal trigger and both sockets were absent
after cleanup. The [structured evidence](research/native-auth-kvm-evidence-2026-09-13.json)
contains this separate trial alongside the earlier prelaunch-renewal evidence.

This is a controlled expired-token fault injected on the trusted side after first
use, not a wall-clock expiry test or real-provider 401 recovery. The internal file
trigger is a private lab mechanism, not a worker capability or production IPC.
No real credentials, inference billing, provider account operation or external
communication was involved. The positive workload remains a shell canary; useful
patch production and independent evaluation must be demonstrated separately.


## Native tool-produced patch and separate evaluator

The positive task now runs the existing version-comparison fixture through the
original Codex tool-execution path, the bounded model channel and the on-demand
synthetic native refresh service. Public pip 25.2 and packaging 25.0 wheels were
hash-checked into the clean seed; installation and candidate code execution occurred
inside the worker. The supplied correction generated a bounded unified patch and
passed six cases while the original lexical comparison failed. Runtime: 52.241s.
The 23 negative probes and exhausted-budget rejection still passed.

Only the candidate artifact was incorporated into a fresh evaluator seed. That VM
independently downloaded the pinned wheels through its restricted public egress,
checked the base/patch hashes and exact single-file fixture hunk, reconstructed the
candidate and passed six different version cases. The original failed. Its patch
hash matches the actual worker output; the evaluator has a distinct fresh nonce
and overlay. Runtime: 43.389s. Both overlays were removed. Candidate code was not
executed on the host. [Structured evidence and patch](research/native-development-evaluation-2026-09-13.json)
are retained without private runtime identifiers.

The model response and correction were supplied fixtures. This is proof of native
tool execution, patch transport and separate execution of independent test cases,
not autonomous problem solving, a real subscription contribution or a productivity
benchmark. Public dependency downloads were in the evaluator; worker research and
model access have not yet been demonstrated together. DAIA receipt submission was
tested separately and is not part of this combined run.
