# Bounded assignment transport

`daia.assignment_relay.relay(connection, helper)` connects an already-open worker
socket to the standard streams of one already-started assignment-only MCP helper.
The trusted launcher chooses both endpoints. Worker data cannot select a helper,
destination, process command, identity or signing key through this interface.

The Linux implementation forwards opaque bytes without logging or parsing them.
Its default total lifetime is 30 seconds and its combined request/response budget
is 256 KiB. Both pipe and socket I/O are nonblocking, including writes. Queues drain
before EOF closes helper stdin or half-closes the reply socket. Excess traffic is
rejected; expiry returns `timeout`, never an indication that a result was recorded.
Only a verified helper receipt establishes submission status.

The function consumes the endpoints and leaves them nonblocking. The launcher
must close them and stop the helper on every exit path, including timeout and
exceptions. The relay is not a process supervisor: an independent service watchdog
must remain effective if the launcher crashes. It supplies no listener, account,
filesystem isolation, destination authentication or admission policy. Run mediation
without administrative privileges; the current elevated lab launcher is not the
production execution design.

Regression tests exercise real sockets and subprocess pipes: bidirectional EOF,
a helper that stops reading, separate and combined traffic limits, and invalid
bounds. Run `python -m pytest -q tests/test_assignment_relay.py` on Linux. These
checks do not establish native-provider confinement or authorize cohort cutover.
