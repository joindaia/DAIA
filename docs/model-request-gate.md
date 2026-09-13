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


## Absolute deadline during active provider traffic

A regression provider sent one response byte every 50 ms. With a 300 ms binding,
the previous inactivity timeout left the request running beyond one second. The
new test failed before the fix. The adapter now uses a deadline watchdog that
revokes and shuts down the active socket; blocking request writes no longer hold
the state lock needed by revocation. Cleanup cancels and joins the watchdog.
The same regression now passes, and the combined request/channel/upstream suite
passes 81 tests. This establishes interruption of continuous local-provider
response traffic, not real HTTPS streaming or a subscription lifecycle test.


## Fixed HTTPS transport prototype

`CodexHTTPSUpstream` adds a fixed `chatgpt.com` TLS peer and
`POST /backend-api/codex/responses` target. The original pinned client declares
this base URL in [model-provider-info](https://github.com/openai/codex/blob/3d2ee51ca2d5db578f328aa75e20aa22c0197c9a/codex-rs/model-provider-info/src/lib.rs).
The controller supplies a public IP literal, token and account binding; the worker
can supply none of these. No DNS resolution, environment HTTP proxy, redirect,
automatic retry or arbitrary request-header forwarding occurs in the adapter.
Host trust roots and launcher environment remain trusted configuration.

A local TLS fixture with a synthetic certificate and token verifies successful
certificate/hostname checking and exact destination/path/headers; separate trials
reject an untrusted certificate, hostname mismatch, redirects and auth failures.
Only test wiring redirects the requested public socket to the loopback fixture.
These tests make no real provider request. The shared adapter retains bounded
responses, deadline interruption, rotation and revocation.

This first transport revision accepted only bounded Content-Length SSE. The
chunked-response extension below removes that framing limitation. It is still not
ready for personal credentials: provider header compatibility,
reasoning continuity, actual account-capability negatives and native subscription
authentication remain unverified. The existing RequestGate must precede it, and
the isolated runtime must enforce public destination policy outside the process.
The transport is not proof of provider approval or exhaustive account confinement.


## Chunked HTTPS responses and public TLS reachability

The adapter now accepts one unambiguous `Transfer-Encoding: chunked` response
without Content-Length, using the standard library HTTP decoder. The decoded body
remains bounded to 8 MiB and is buffered before any output reaches the worker.
This supports HTTP chunk framing, not incremental SSE delivery to the client.
The same literal credential check covers tokens split across chunks. Unsupported
transfer encodings, duplicate transfer headers, mixed framing, truncated chunks
and over-limit bodies are rejected. The existing assignment watchdog interrupts
a continuously arriving TLS chunk stream without allowing another request.

The combined request/channel/upstream/TLS suite passes 110 tests. This includes a
local trusted test certificate, synthetic credentials and a 300 ms deadline with
a provider sending another chunk every 50 ms. No actual subscription was used.

A separate public-network check resolved chatgpt.com, confirmed public IP results
and completed certificate-verified TLS 1.3 handshakes to two returned addresses,
with SNI/hostname verification for chatgpt.com. It sent **zero HTTP requests** and
used **no credentials**. This proves reachability from the development execution
environment, not from the final restricted gateway service or worker VM. It does
not prove Responses compatibility, login, subscription use or account confinement.


### UTF-8 SSE media type

The response gate also accepts a single SSE Content-Type with an explicit UTF-8
charset, including a quoted charset and case-insensitive media type. Missing or
duplicate Content-Type, another media type, a non-UTF-8 charset or repeated
parameters remain rejected. The combined transport/gate suite passes 117 tests.
This is protocol compatibility tested with synthetic credentials, not evidence
that a real subscription request succeeded.


## First real subscription attempt: model rejected

On 13 September 2026, the participant completed the original pinned Codex client's
device authorization in a separate host-side profile. Native login reported
success. Its credential file was mode 0600; no auth profile, access token or refresh
token was included in the VM seed. Only a short-lived access-token/account binding
was handed to the restricted external gateway in a private file, consumed and
unlinked. The participant's refresh state remained in the trusted native profile.

Two fresh-overlay KVM runs used the original client and the fixed HTTPS adapter.
Each ran the 23 hostile channel probes before attempting the controlled public
version-comparison task. All probes were denied. Each made exactly one provider
request and received HTTP 400; neither completed a model turn or produced a patch.
The second run retained the error privately to identify the cause. Exact comparison
confirmed the provider's error: the requested `gpt-5.3-codex` model is not supported
when using Codex with a ChatGPT account. No raw credential, account identifier or
private provider error record is published.

Worker runtimes were 39.400 and 44.423 seconds. QEMU completed successfully but the
**native model client exited 1**, so these are failed model trials, not successful
development jobs. Both overlays were removed and services stopped. The same
approved seed was used for both attempts; runtime overlays were separate.
The gateway was configured with a deny-all IP policy plus the single resolved
public provider IPv4 address. This trial did not independently prove enforcement
of that kernel policy against private-network canaries.

This establishes a real login and an actual provider response through the KVM-to-
HTTPS path. It does not establish model entitlement, inference success, account
confinement across all provider features, refresh/revocation, a tested fix or a
DAIA receipt. The next prerequisite is a supported model selection from the native
client, followed by another bounded trial. No API billing fallback was used.


## First successful Spark subscription contribution

The participant suggested `gpt-5.3-codex-spark` after the first model was rejected.
Two attempts reached HTTP 200 but were deliberately blocked because this provider
response omitted Content-Type. Private header inspection confirmed the omission
and a distinct active limit labelled GPT-5.3-Codex-Spark. No personal usage values,
cookies, account IDs or opaque turn state are published.

For the fixed certificate-verified Codex endpoint only, absence of Content-Type
now requires a fully buffered, UTF-8, structured Responses SSE stream with matching
event/data types and a completed response before anything is released. Present but
invalid or duplicate media types remain rejected. Truncated, malformed, duplicate-
key, mismatched and non-Responses data fail closed. Size, credential and deadline
checks are unchanged. The transport/gate suite passes 123 tests.

The subsequent one-request trial completed a real native Codex turn inside KVM
using the participant's subscription. The client proposed a fix for a controlled
public numeric-version fixture. All 23 channel negatives remained denied. Runtime
was 49.552 seconds; native exit was zero and the overlay was removed.

The model returned apply-patch-style text rather than the requested unified diff.
A fresh evaluator VM extracted the single-file proposal under a strict fixture
envelope check and checked the function's syntax before executing it. The proposal
code was unchanged. Ten independently supplied regression cases passed; the
original function failed. The evaluator had no network device or provider credential
input, used no model and removed its overlay. Runtime was 38.368 seconds.
[Structured evidence, actual proposal and limitations](research/first-spark-subscription-trial-2026-09-13.json).

This is real subscription-backed code generation with separate functional
evaluation. It is not the full goal: research, model-driven tool execution, real
refresh/revocation, independently tested private-network enforcement and DAIA
receipt submission still need to be combined and verified. A distinct Spark limit
is observed for this account, not a promise about every participant's entitlement,
available quota or provider terms. No fallback to API billing or another model was
used. A worker must not silently switch model or quota when this route is exhausted.


### Multi-turn Spark follow-up (2026-09-13)

A real Spark turn executed a successful `ls` command inside a fresh KVM worker.
The next request was refused before forwarding: its frozen configuration matched,
but it contained a reasoning item with encrypted content and an assistant message
with a phase. The worker did not modify the source or finish the development task.
Twenty-three model-channel negative probes were denied in that run. The overlay
was removed. This is evidence of real tool execution, not a completed coding job.

The request gate now has an explicit trusted-controller method to register exact
provider reasoning items for one assignment. Only their canonical SHA-256 digests
are retained, with a maximum of 64 entries; registration is atomic. An incoming
reasoning item must match a recorded item, including its summary and encrypted
content. Optional IDs are removed before comparison/forwarding. A new assignment
requires a fresh gate. Workers must never be able to call the registration method.
Assistant phases are restricted to commentary/final_answer; other roles cannot
supply them. Regression cases cover foreign assignments, changed content/summary,
unknown phases and registration limits.

This mechanism is not yet a working multi-turn subscription integration. In the
private live harness, registering only `response.completed.output` admitted zero
reasoning items. A subsequent attempt to register completed output items refused
the provider response. Its precise item shape remains unverified. A diagnostic
retry stopped during the negative-probe preflight with an empty reply, before any
provider request, and produced no valid worker report. Do not count that retry as
a model, isolation or development success. Do not loosen validation to accommodate
an unknown shape. Next: reproduce the preflight failure without credentials, then
capture only safe provider item schemas and test the missing representation.

Validation: 129 focused model-gateway tests passed; the full suite passed with
520 passed and 10 skipped. A preceding full-suite attempt in the restricted shell
could not run socket-based fixtures and was terminated; the successful run used
local socket permissions. No full account-confinement, refresh, or combined DAIA
receipt claim follows from these results.


### Successful native Spark tool round (2026-09-13)

The earlier preflight failure led to a reproducible relay defect: an upstream
that rejects a request while the guest is still uploading can leave a buffered
403 reply, but the old relay exits immediately on a broken write. The lab relay
now stops uploading and drains the response. The regression fails with the old
stop-on-write-error behavior. A fresh credential-free KVM preflight subsequently
received all 23 expected rejections, with zero model calls and overlay removal.
The checked-in relay is `scripts/model_channel_bridge.py`; it has a fixed local
socket destination and no worker-selected endpoint.

The provider reasoning item included an additional `content` field. Registration
now permits dropping that field only when empty (null or an empty list), on the
trusted provider side. Nonempty content remains denied. Completed output items
are registered after the full provider stream has passed validation, rather than
relying only on the final completion's output array. Exact reasoning/summary
binding and the per-assignment limit remain in effect.

With these changes, the original native Codex client using a real Spark
subscription completed a coding round in a fresh KVM: five successful terminal
commands inspected files, applied a patch and ran the supplied four-case test.
The test file was unchanged. Six provider requests were forwarded; 23 hostile
channel probes were refused. The client completed with exit zero in a run lasting
57.946 seconds. Its event stream also contained a nonfatal error item, so this is
not a claim of an error-free client startup.

The exact resulting source, without edits or patch-format normalization, passed
ten separately supplied regressions in another fresh VM with no network device
or provider credentials. The original source failed. Evaluation took 38.148
seconds; both overlays were removed. The evidence file
[records the source and its hash](research/spark-native-tool-trial-2026-09-13.json).

Current regression result: 524 passed, 10 skipped, one existing warning.
This establishes real subscription-driven file editing and test execution for a
controlled fixture. Public research, dependency downloads, the DAIA receipt,
refresh/revocation, and complete account/network confinement are still not proven
as one combined workflow. The public cohort gate remains closed.


### Shared provider stream parsing

`model_response.completed_output` now performs the bounded complete-stream parse
used by both the HTTPS adapter's missing-content-type check and the lab controller's
reasoning registration. It gathers `response.output_item.done` items as well as
final completion output. It returns nothing until the whole stream is valid;
truncation, malformed events and events after completion fail before registration.
The controller must still authenticate the response through its fixed upstream
binding and use a fresh request gate per assignment. This helper alone does not
prove provider authenticity or authorize worker-supplied streams.

Regression coverage includes the observed empty-content reasoning shape, an exact
multi-turn round trip, foreign-assignment rejection and no state admission from a
partial response. The live lab launcher was updated to use the shared parser;
that launcher change has been syntax-checked, not rerun against the subscription
in this change. The preceding live Spark evidence remains the evidence for model
execution. No new provider request was made for this refactor.

Validation for this refactor: 531 passed, 10 skipped, one existing warning.


### Preparing the combined assignment and model round

A new source-evidence regression uses real local MCP/HTTP requests to submit an
assignment-bound packet, then deliberately loses the committed receipt. A fresh
Contributor instance rejects a changed retry and recovers the exact pending
submission after the original consent deadline. The coordinator retains exactly
one result, no promotion occurs, and identity, job count and deadline remain
unchanged. This is an in-process helper restart against a real HTTP service, not
a VM restart or an additional live-model run. The existing factorization recovery
test did not by itself establish this source-evidence path.

The two standalone VM harnesses currently reuse virtual address
`10.0.2.100:3128`, so they cannot simply be concatenated. The combined trial must
keep that fixed assignment endpoint and give the model channel a separate fixed
virtual endpoint, for example `10.0.2.101:3128`, mapped by the trusted launcher to
a different Unix socket. Neither bridge may accept a worker-selected host path,
URL, destination or credential. Guest protocol enumeration must exercise both
channels and prove that model traffic cannot invoke assignment/operator functions.
This is the next launcher integration, not an already tested dual-channel claim.

Create the synthetic local assignment and frozen source before the live model
runs; do not retrospectively describe the earlier Spark fixture as work obtained
from DAIA. Preserve independent patch evaluation and the distinction between an
accepted source-evidence packet and a proven correct patch. The combined trial
must show an unchanged pending payload, a refused modified retry, one recovered
receipt and no extra consent or job consumption.

Validation: 34 assignment-host, source-evidence and assignment-relay tests passed.


### Two channels in one KVM: credential-free integration

The fixed assignment endpoint and a separate model endpoint were exercised in
one fresh KVM. A synthetic local source-evidence assignment was admitted before
execution, with a bounded invitation and signed assignment authority. This did
not reuse or extend an existing participant grant. The non-root assignment helper
ran in its existing private service root; worker and egress identities could not
read its saved state.

The model endpoint at `10.0.2.101:3128` returned one synthetic response and denied
23 hostile requests, including MCP enumeration and authority-changing bodies.
The assignment endpoint at `10.0.2.100:3128` exposed only heartbeat/submit_result;
claim, registration, consent-stop and an invented model tool were denied. It
accepted a source-bound packet, deliberately lost the committed receipt, refused
a changed retry and returned the existing receipt for the exact retry. The local
coordinator retained one result and the helper cleared pending state without
changing identity, deadline or job budget.

The run completed in 43.086 seconds and removed the guest overlay. See the
[bounded result record](research/dual-channel-vm-trial-2026-09-13.json).
An initial setup attempt was correctly refused because the synthetic source path
was outside the accepted src/tests/docs roots; fixing the fixture path did not
change admission policy.

No native model client or provider credential was used in this combined trial.
It proves tested channel separation and receipt recovery, not the complete live
subscription workflow or general host/account confinement. The next integration
must replace only the synthetic model endpoint with the existing fixed Spark
binding while keeping the source assignment and helper authority established
before execution. Preserve the separately tested external credential service,
its resource/network limits, and independent evaluation; do not move credentials
into this synthetic parent process merely to combine harnesses.


### Real subscription plus assignment receipt in one worker

A new local source-evidence assignment and finite contributor grant were created
before booting the combined worker. The fixed model channel used the existing
separate credential service, public destination pin and resource/network policy;
the assignment channel used its non-root private helper. No existing participant
grant was extended and no credential was put into the guest seed.

The original Codex client with Spark read the two supplied source/test files,
applied a change and ran the unchanged test file. It completed with exit zero
using four provider requests and three terminal commands. The model channel also
refused the 23 hostile preflight requests. The guest harness then constructed a
source-bound evidence packet containing the exact resulting source and invoked
the scoped helper. The helper deliberately lost the first committed receipt;
a changed retry failed and the exact retry returned the existing receipt. The
coordinator stored one result, still in_review. Identity, deadline and job count
were unchanged and pending state was cleared.

A read-only query of the actual local coordinator database confirmed that the
stored proposed source exactly matched the worker output. Those same bytes passed
ten separately supplied regressions in another fresh VM with no network device
or provider credentials. The original source failed. Worker and evaluator took
56.304 and 44.016 seconds respectively, and both overlays were removed. See the
[combined result record](research/live-subscription-assignment-trial-2026-09-13.json).

The first attempt reached the six-request ceiling; the seventh request was denied
and nothing was submitted. The successful run used a narrower exploration prompt,
not a higher limit. This is a real subscription development-and-delivery trial,
but remains a controlled fixture with harness-driven submission. It does not prove
public research, downloads, native provider refresh/revocation, comprehensive
private-network or provider-account confinement, production scheduling, or an
automatically accepted repository improvement. Keep those release gates open.


### Native subscription refresh and TLS revocation

The pinned original Codex 0.153.4 app-server was started on the trusted host
with the already authorized dedicated participant profile. The documented
`account/read` operation with `refreshToken: true` returned a ChatGPT account;
both saved access and refresh credentials changed, the account binding stayed
the same and credential-file permissions remained private. A second fresh
app-server process read the persisted account without forced refresh; both
credentials remained unchanged and both processes exited zero. No raw account
response or credential was published. No model turn, guest or new login occurred.
See the [bounded record](research/native-subscription-refresh-2026-09-13.json)
and [official account API documentation](https://learn.chatgpt.com/docs/app-server).

This establishes live native refresh and persistence across an auth-client
restart. It does not yet establish a guest inference request spanning refresh,
provider-side logout/revocation, or complete account confinement. Account metadata
is not by itself evidence that a subsequent model request will be authorized.

Separately, 62 HTTPS/upstream tests passed. The added local TLS tests confirm
that explicit binding revocation interrupts an active dripping response within
one second, rejects subsequent requests and cannot be reversed by replacing the
credential. Between requests, trusted credential replacement preserves the fixed
account, destination, deadline and request budget. These use synthetic credentials
and a local TLS fixture, not provider-side token revocation.


### Real worker continues across native credential refresh

A fresh KVM source-evidence trial now spans real credential replacement. After
one successful Spark request, the external model service paused the next call.
The trusted controller invoked the pinned original Codex account/read refresh
and restarted that auth client; it checked the unchanged account before delivering
only the new access credential through a private, consumed handoff. The model
service retained the same binding, reasoning history, destination, 150-second
deadline and six-request budget. No refresh credential entered the service or VM.

The native guest completed development in five provider calls and three terminal
commands, leaving the supplied test unchanged. The 23 negative preflights were
refused. The harness submitted the exact source through the assignment helper;
a deliberately lost receipt, refused changed retry and successful exact retry
left one in-review result, with no extra consent or identity change. A direct
read-only database check matched the stored source to the worker. The same bytes
passed ten regressions in a fresh evaluator with no network device; the original
failed. Both overlays were removed. Worker runtime was 63.153 seconds.
See the [bounded record](research/live-subscription-rotation-2026-09-13.json).

Three earlier attempts stopped after one provider request and submitted nothing.
Diagnostics isolated a harness reporting failure: the native refresh helper tried
to overwrite an existing temporary file owned by a different user. WSL refused
that write, so the controller treated refresh as failed and withheld replacement.
Removing the unnecessary report write fixed the trial; filesystem protections and
request limits were not relaxed. A failed refresh/handoff still fails closed.

This establishes development and idempotent delivery across a real managed-auth
refresh and auth-client restart. It does not establish a guest restart, public
research/download in the same run, provider-side revocation, comprehensive account
confinement, or a packaged production controller. Submission remains harness-driven.


### Research, dependency use and real subscription in the same worker

A third fixed guest endpoint now reaches a separate credential-free public-egress
service under its own runtime identity and private service root. Its only allowed
hostnames were docs.python.org, pypi.org and files.pythonhosted.org; it reused
public_egress resolution/address checks and host-interface exclusions. The model
and assignment endpoints retained their existing bindings. The research service
had no model-secret directory mount and could not read saved assignment state.

The native agent invoked the [guest research fixture](../scripts/probe_public_research.py),
which fetched Python stdtypes documentation and packaging 25.0 metadata/wheel over
end-to-end TLS. The wheel matched the digest in the retrieved metadata and was
imported directly inside the VM for two version comparisons. The agent inspected
the downloaded documentation, patched the source using only the standard library
and ran the unchanged tests. This is real download and dependency use, not a
general package-manager or arbitrary installation-hook test. The helper selected
the URLs in advance; no claim of unconstrained autonomous research is made.

The same run completed native credential refresh after the first provider call,
then finished within four provider calls and three terminal commands. Twenty-three
model-channel negatives and six research CONNECT negatives were refused. The
latter covered loopback, metadata, CGNAT, IPv6 loopback and the two provider hosts;
these were authority refusals, not live DNS-rebinding probes. Separately, all 29
public-egress unit tests passed, including mixed-address resolution and numeric
pinning. Those fixture tests do not replace live private-network canaries.

Exact receipt recovery retained one in-review result with unchanged consent. A
database check matched the stored source to the guest output, and those unchanged
bytes passed ten independent regressions in a fresh networkless evaluator while
the original failed. Both overlays were removed. Worker runtime was 65.992 seconds.
See the [bounded result record](research/live-subscription-research-2026-09-13.json).

Remaining gates include comprehensive live host/private-network/account negatives,
guest restart and crash cleanup across all three channels, provider-side revocation
semantics, installation hooks, and a reproducible packaged controller. This trial
does not authorize an open cohort or weaken any existing admission policy.


### Controller crash propagation: verified gap and supervisor fix

The combined private harness previously created independently supervised model,
research, assignment-helper and worker services. Normal Python cleanup stopped
these, but SIGKILL cannot run atexit handlers. RuntimeMaxSec bounded their eventual
termination; it did not make them stop when the controller failed. Earlier clean
shutdown trials must not be treated as evidence of crash propagation.

The credential-free [systemd lifecycle probe](../scripts/probe_job_lifecycle.py)
reproduced this gap with four live synthetic Unix endpoints. After killing the
controller main process, all four unbound services remained active. With BindsTo
and After pointing at the controller, KillMode=control-group, Restart=no and a
bounded stop timeout, all four endpoints became unreachable and ExecStopPost
removed their synthetic temporary files in 1.179 seconds. Children deliberately
ignored SIGTERM and spawned descendants. The probe requires a privileged lab;
it does not launch a VM, use credentials or prove network isolation.

The private combined-run candidate now requires a dedicated controller unit and
adds these dependencies to all four transient children. Worker overlay removal
and research socket deletion have supervisor-side ExecStopPost actions. The
controller's own unit must also clean its assignment endpoint and private
credential-handoff files; those parent-owned files are not automatically removed
by child dependencies. Never delete the persistent contributor state needed for
pending-result recovery as part of disposable worker cleanup.

This candidate has been syntax-checked, not yet run through a hard-crash KVM test.
The next acceptance run must terminate the actual controller without Python
cleanup, observe QEMU and all service cgroups terminate, verify model/research/
assignment endpoints are inaccessible and ensure the disposable overlay is gone.
Use synthetic credentials and no paid model requests for that destructive probe.
Test ordinary success separately after wiring the supervisor. The open cohort
and production-controller gates remain closed pending this evidence.


### Hard controller crash with a real KVM and three channels

The bound-run candidate passed an external crash test. A fresh KVM booted with
only synthetic model credentials. The guest obtained explicit refusal responses
from the model and research endpoints and successfully initialized the scoped
assignment helper, then remained running. No model request or provider refresh
was attempted; model egress was denied and the research allowlist was empty.

Before the crash, the outside observer verified that all four child services were
active, the five service cgroups were populated, one actual QEMU process existed
in the worker cgroup, the overlay existed and all three socket paths existed.
It then killed only the controller main process with SIGKILL. Within 0.105 seconds
all five cgroups were empty, connection attempts to every endpoint failed, and
the overlay and transient handoff paths were absent. An atexit marker was absent,
confirming Python cleanup had not run. See the
[bounded record](research/kvm-controller-crash-2026-09-13.json).

The tested arrangement uses BindsTo plus After on all children, control-group
termination and bounded stop timeouts. The worker has supervisor-side overlay
removal; model/research services remove their sockets. The controller unit's
ExecStopPost removes its assignment socket and transient credential handoffs.
Persistent contributor state is retained for recovery, not erased alongside the
VM. This distinction is required even when the controller cannot run cleanup.

This supersedes the earlier missing hard-crash evidence for the lab candidate,
not the remaining production gates. A successful ordinary run under this exact
supervisor wiring, pending-artifact recovery after a hard crash, and in-flight
live-subscription revocation remain separate acceptance tests. The controller
harness is still private lab infrastructure rather than a packaged runtime.
