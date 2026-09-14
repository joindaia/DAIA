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
