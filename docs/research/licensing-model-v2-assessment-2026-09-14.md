# Licensing model v2: maintainer assessment

14 September 2026. The emailed research assessed PR #21 at
`840298b5d4e3d6ce0279e10328e7b06f00170057`, which was still its head when checked.
For this licensing review the baseline is current; it is not the older worker
architecture discussed in the separate security research.

**Decision:** on 14 September the owner explicitly chose retained contributor
copyright and permission for a founder-owned company to issue commercial licences.
The [selected design](../licensing-model-v2.md) replaces the prior mandatory
assignment and foundation-only route. The complete official Core remains AGPL.
The former direction remains accessible through its original commit; it is not
rewritten as if this were always the policy. No existing signed grant is amended.

This selects a design, not a legal counterparty or an operative programme. No
company is appointed, agreement executed, commercial release cleared or payment
authorized by this change. Actual instruments and release evidence are still needed.

## English summary and judgment

The [supplied report](licensing-model-v2-source-2026-09-14.md) recommends retained
contributor copyright with explicit nonexclusive commercial and patent permissions
for accepted Core work. An identified incorporated company or foundation would be
the licensor. A contractual covenant would keep the complete official Core and
licensor-controlled Core improvements available under AGPL-3.0-or-later, including
official hosted use. Independent customer work remains outside that grant.

This is a credible way to obtain proprietary licensing permissions. It is not
equivalent to ownership, independent governance, universal enforcement standing,
or a clean chain of rights. An ownership transfer is not necessary merely
for dual licensing; centralized ownership was a separate objective selected by
the owner. A company recipient is also a separate governance choice: it permits
founder control and possible shareholder benefit, unlike the previous independent
foundation bargain. Neither choice follows merely from the feasibility of the grant.

Given the newly confirmed objective of sufficient licensing authority, I recommend
and adopt the retained-copyright route, subject to properly executed instruments.
The company route follows the owner's governance choice, not a legal requirement.
A company may benefit shareholders; disclose that before contributor assent rather
than carrying forward an independent-nonprofit promise. No salary or dividend is
approved here. Existing restricted donations and executed agreements retain their terms.

## What the primary sources support

- [Qt's contribution guidance](https://www.qt.io/community/legal-contribution-agreement-qt)
  confirms that contributors retain ownership while granting rights to The Qt
  Company. It distinguishes corporate authorization and enforcement. This is a
  relevant precedent, not validation of a Dutch DAIA agreement.
- [Staatsblad 2025, 352](https://zoek.officielebekendmakingen.nl/stb-2025-352.html)
  requires written agreements for assignment or exclusive licensing and retains
  a deed for delivery of assignment. The [commencement decision](https://zoek.officielebekendmakingen.nl/stb-2025-392.html)
  gives 1 January 2026. The new report correctly preserves the earlier correction.
- [AGPLv3](https://www.gnu.org/licenses/agpl-3.0.dbk) permits commercial use subject
  to its conditions. It does not provide a recipient with general authority to
  license other people's covered code under proprietary terms. The proposed
  licensor covenant is a separate agreement, not an amendment to the public licence.
- [KVK's comparison](https://www.kvk.nl/starten/een-eenmanszaak-of-bv-als-rechtsvorm-kiezen/)
  distinguishes a BV's legal personality from a sole proprietorship and describes
  shareholder distributions. It does not establish a DAIA company, authorize a
  payout or settle the proposed transfer and insolvency terms.
- The [official explanation of future-work clauses](https://zoek.officielebekendmakingen.nl/kst-33308-C.html)
  describes contextual reasonableness, not a universal safe duration. The proposed
  12-month participation window and 60-day cure period remain drafting choices.

The full international scope, mandatory author protections, electronic assent,
employer/patent authority, successor transfer, customer sublicence survival and
insolvency effects have not been legally validated by this engineering review.
The research itself correctly leaves these matters open.

## Changes that do not depend on the governance choice

Keep legal participants separate from workers. Identify the actual rights holder
and employer authority; bind prospective Core scope and revocable worker consent
before work starts. Acceptance must identify exact content and its inclusion.
Reclassifying an external job, merging a PR or signing with a worker key does not
create a missing grant. Direct human and legacy submissions need their appropriate
route rather than fabricated worker records or backdated consent.

The rights map must include surviving inherited material, copied hunks, dependencies,
build outputs and notices, not just a file's last author. Private identity and
agreement records should be referenced by opaque identifiers. A preview may detect
inconsistent records, but neither an identifier nor a passing check authenticates
the underlying evidence or prevents a privileged maintainer from lying.

The supplied offline checker and tests are now included. It compares two supplied
JSON descriptions, requires exact artifact coverage and hashes, checks record and
reference syntax, and refuses unresolved Core statuses. It always reports
`commercial_release_authorized: false`; `--release` always exits 2.
See the [preview contract](../licensing-rights-register.md#offline-consistency-preview).

Two limits are made explicit in this integration: the tool does not read a release
tree or independently produce its inventory, and its licence-label check does not
validate membership in the SPDX registry or legal compatibility. A syntactically
plausible invented label can pass. Building an authenticated release gate or adding
a licence database is outside this bounded change.

## Actionable follow-up

| Item | Next concrete result | Status |
| --- | --- | --- |
| Governance decision | Owner chooses ownership versus sufficient grants, and foundation-only versus company recipient | Confirmed: retained copyright and company licensing; design updated |
| RIGHTS-01 | Freeze Core scope, classify work before dispatch and define acceptance/withdrawal events | Detailed research available; runtime enforcement still open |
| RIGHTS-02/03 | Identify the actual counterparty and prepare reviewed individual, organizational, founder and successor instruments for the chosen model | Open; no executed instrument or new legal entity |
| RIGHTS-04/05 | Authenticate private assent and rights evidence, reconcile changed content and revocation before acceptance | Open; the offline preview supplies none of these powers |
| RIGHTS-06 | Independently inventory an exact release and reconcile inherited, generated and third-party material | Consistency preview implemented; historical/actual-release rights audit open |
| RIGHTS-07 | Obtain an authorized legal clearance and matching public AGPL source before issuing alternative licences | Closed to release; no automatic activation |

## Provenance and validation

The separate Markdown attachment matches the model document in the supplied ZIP.
All 16 proposed file digests match its manifest, and the repository ID was checked
against GitHub. These checks establish package consistency, not authorship or title.
All 16 proposed file changes were integrated after review and the owner's explicit
choice, with this assessment, an archived source report, clarified preview limits
and two additional regression checks. The supplied mass-apply script was not run.
The inactive programme configuration, contribution guidance, grant architecture,
founder/successor schedules, roadmap, PR template and licence page now agree.
The configuration is documentary; neither changing it nor a passing preview can
activate a contract or commercial licence.

The imported research and prototype are not marked proprietary-cleared by this
change. No private sender identity, mail header, agreement or credential is published.
The earlier ownership decision is linked at its original immutable commit.

Validation of the integrated change:

- Full local Python suite: 405 passed, 10 skipped, 14 subtests passed; one dependency
  deprecation warning. Skips include optional native/namespace/Nginx integrations
  and Windows-specific file-sharing cases, not successful execution of those cases.
- New checker suite: 14 tests passed separately on Linux and native Windows Python,
  including the two additional checks for refreshed inventories and label limits.
- Deterministic demo, Python compilation, local Markdown links and whitespace checks
  passed. The original `LICENSE` file is unchanged.
- Website dependencies were installed from the existing lock without install scripts;
  the static website build succeeded, including the updated licence page.
- No actual contract assent, private rights clearance, provider call, licence sale
  or production website deployment was performed. GitHub CI is checked separately
  after publication; local success is not a claim about a future CI run.
