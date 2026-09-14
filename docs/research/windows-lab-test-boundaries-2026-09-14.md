# Windows CI and Linux lab test boundaries

The Windows reference job for source `1fdfef1c273f05ae31077e7781264a1e1ddaad84`
failed during collection: the Linux service-identity test imported `pwd`, which
Windows does not provide. Ubuntu reference checks and the website build succeeded
for that source. The failed job did not run the test suite to completion.

The test selection now explicitly limits Linux service identities and private
profile/run filesystem checks to Linux. These assertions depend on Linux account
lookup, ownership, permission bits, directory descriptors or directory fsync.
The runtime checks and authority policy are unchanged. Pure outcome classification,
receipt binding and summary tests still run on Windows; the combined private-write
case was split so its portable outcome assertion remains exercised there.

Validation before publication:

- Linux: 68 selected identity, authentication, outcome, inspection, authority,
  shutdown and request-ledger tests passed.
- Native Windows Python: the same selected modules produced 4 passed and 23
  reported skips, with Linux-only module skips counted by pytest. This focused
  run disabled unrelated conftest/plugin loading and reused the installed pure
  Python pytest libraries; it is not a full Windows dependency or CI run.
- An initial focused Windows invocation failed because the shared general
  conftest loaded Linux cryptography binaries; it is not counted as a pass.

Full GitHub Windows CI must run again on the resulting commit. These test guards
neither implement a Windows subscription lab nor establish VM, provider-account,
credential or network confinement. No live provider or participant job was used.

## Follow-up after full Windows CI reached execution

The Windows job for `cf3b79c94a7944babfc0bc53e5f3635e6565901d` passed collection
and exposed additional test-harness and platform assumptions. Ubuntu reference
checks and the website build succeeded. The
[Windows job](https://github.com/joindaia/DAIA/actions/runs/34803033512/job/103849360887)
failed; this is not a successful full Windows run.

The follow-up changes are limited to tests:

- Oversized-input cases retain their original payloads but use short parameter
  IDs. This avoids exceeding Windows environment-variable limits when pytest
  writes the current test name.
- Private profile ownership, Linux evaluator service properties, and the Linux
  diagnostic wrapper have explicit Linux guards. Portable bundle assembly and
  wrong-binary rejection checks remain selected on Windows.
- Model-channel round trips now explicitly use Unix-domain sockets, matching
  the deployed lab listener and bridge. On the tested Windows Python build,
  `socketpair()` instead uses TCP, where closing with unread input can reset a
  queued denial response. The tests skip when Unix-domain sockets are absent;
  they retain all denial and forwarding assertions on the supported transport.
  The in-memory partial-response writer check remains portable. These changes
  do not establish a supported or tested Windows TCP model transport.

Validation of these changes before publication:

- Linux: all 56 tests in the five affected modules passed.
- Native Windows Python: 8 passed, 47 skipped, and 1 failed. The remaining local
  failure is the bundle test attempting to create a symbolic link without the
  required Windows privilege (`WinError 1314`). The test remains enabled; the
  previous GitHub Windows run did not report this prerequisite failure.
- The focused Windows run used a fresh temporary directory, disabled unrelated
  conftest/plugin loading, and reused installed pure Python pytest libraries.
  An earlier invocation failed on the shared temporary-directory permissions;
  it is not counted as a pass. This is partial local validation, not full CI.

Full GitHub CI on the follow-up commit remains required. Runtime code and security
policy are unchanged. No live provider request or participant job was run for
these test corrections.
