# Experimental public egress

`src/daia/public_egress.py` implements one bounded CONNECT connection, not a
production listener or an account gateway. An operator supplies exact lowercase
DNS names and excluded host-network CIDRs outside the worker. Only port 443 is
accepted. Every returned address is checked before any connection; non-public,
multicast, reserved, scoped and selected IPv6 transition addresses are rejected.
The socket connects to a checked numeric address without a second DNS lookup,
and its actual peer address is checked.

The implementation bounds headers to 4096 bytes and five seconds, and each tunnel
to 30 seconds and 8 MiB in both directions combined. TCP half-close preserves the
remaining response direction. OS DNS resolution still needs an independent
service deadline. The surrounding service must bound concurrency and resources,
protect its Unix socket and policy, and exclude private host networks independently.
No public TCP listener, provider credential injection or contributor admission is
provided by this module.

TLS is opaque and validated by the client. An allowed DNS name restricts which
socket addresses are selected; it does not enforce SNI, HTTP paths, or account
operations inside that tunnel. Shared/CDN endpoints can serve other names.
Never treat this as an inference-only gateway or use it to expose personal
provider credentials. Redirects that create another CONNECT require a new
authorization; actions within an existing encrypted connection are not inspected.

## Evidence on 13 September 2026

Twenty-nine local tests cover mixed public/private DNS sets, IPv4/IPv6 exclusions,
operator host-network exclusions, numeric address binding, peer mismatch cleanup,
authority rejection, preserving TLS bytes after headers, body rejection, header
limits, half-close, byte limits and idle timeout. Static review found the original
half-close bug; it was fixed and exercised with actual socket pairs.

A real KVM guest used a private network namespace and a fixed Unix-socket bridge.
A separate non-root gateway service admitted only `joindaia.com` and excluded the
host's interface networks. The guest validated TLS, received HTTP 200 and 19,058
bytes containing DAIA site content. A CONNECT to a loopback address received 403.
The guest exited successfully and its overlay was removed. No provider secrets,
account login or arbitrary external destination were used.

The first run failed because WSL's resolver file lives under the hidden `/mnt`
mount. The gateway was moved into a minimal service filesystem root containing a
fixed resolver copy, read-only runtime/code and the explicit writable socket
location. This restored DNS without exposing the personal filesystem. The gateway
service and socket were stopped/removed after the probe.

This is a working public-site prerequisite. It does not establish hostile-job
containment for every network route, complete DNS/redirect attack coverage,
provider integration, package installation, a useful native-agent task or release
readiness. The surrounding service harness is still a private lab fixture; the
module has not been merged, deployed or exposed to contributors.
