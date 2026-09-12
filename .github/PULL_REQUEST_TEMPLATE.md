## Objective and scope

Link the admitted issue/contract and frozen baseline. State whether this affects a protected boundary.
Name the bounded acceptance criteria and the work type: source analysis or a trusted local code change.
Source-analysis pilot reviews are technical feedback, not independent verification or merge authority.

## Evidence

List commands actually executed and their results. Separate local tests from untested MCP, Windows, PostgreSQL or production behavior. Include independent reproduction where required. Do not paste sensitive logs or credentials.

## Invariants and privacy

Explain changes to assignment eligibility, owner conflicts, leases, signatures, evidence policies and personal-data handling. Run the privacy guard. Do not modify acceptance rules to make this PR pass.

## Maintainer decision

Agent and pilot review are evidence, not merge or deployment authorization. A human maintainer
must decide whether to merge after reviewing the criteria and evidence.
