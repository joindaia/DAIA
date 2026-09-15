# Gemini CLI subscription worker candidate

Status: candidate, not implemented or tested. Codex remains the active reference
worker; Gemini is not a prerequisite for its release gates.

The official Gemini CLI authentication guide, checked 2026-09-13, explicitly
instructs Google AI Pro/Ultra subscribers to sign in with the Google account
associated with their subscription. This establishes a supported native-client
subscription login route, not DAIA worker isolation or provider approval for a
specific delegated-work service.

Source: https://geminicli.com/docs/get-started/authentication/

Before a trial: pin the original client and inspect its OAuth scopes, token cache,
refresh path, inference endpoints and non-inference account capabilities. Determine
whether native subscription use works with credentials held outside the guest.
Do not upload Google credentials to the coordinator or silently substitute a paid
API. Test isolation, account-function denial, expiry/revocation and one bounded
public development task with independent evaluation. No real login or subscription
usage is authorized merely by recording this candidate.
