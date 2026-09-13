# DAIA Core ownership: assessment and decision

Decision date: 13 September 2026. Maintainer decision under the owner's instruction.
**Status: selected policy direction; no assignment executed, no foundation established
by this document, and no commercial release cleared.** The public AGPL licence is unchanged.

## English summary of the two reports

The [licensing structure review](research/licensing-structure-review-2026-09-13.md)
and [Core rights review](research/core-rights-review-2026-09-13.md) recommend keeping
contributors' copyright while obtaining broad supplemental rights for a future
independent foundation. This can support dual licensing without collecting all
copyright. Both reports correctly distinguish AGPL use from proprietary relicensing,
identify employer and third-party rights, and reject Git metadata as ownership proof.
Their strongest operational proposal is to bind a real rights holder's agreement
to defined, accepted Core contributions, rather than treating everything an agent
produces as project property.

Their preferred structure solves licensing authority, but does not deliver the
owner's stated objective that accepted DAIA Core work becomes DAIA-owned. We adopt
their provenance, scope and governance safeguards, but do not adopt retained
contributor ownership as the default destination for new original Core contributions.
An assignment is harder to administer and may deter contributors. That cost is
explicitly accepted as a consequence of choosing centralized ownership.

## Material correction to the research

Dutch law changed before these reports were prepared. Article I.A of the
[Wet versterking auteurscontractenrecht](https://zoek.officielebekendmakingen.nl/stb-2025-352.html)
requires a written agreement for copyright transfer or an exclusive licence;
delivery of the transfer still requires a deed under BW 3:95. The
[commencement decision](https://zoek.officielebekendmakingen.nl/stb-2025-392.html)
sets 1 January 2026. Thus a statement that both routes still require the same
copyright deed is outdated. This does not make a GitHub checkbox sufficient for
assignment, nor establish that any proposed electronic signature or future-work
clause is valid. Those instruments need jurisdiction-specific review.

The reports' internal citation identifiers lack their source mapping. Their legal
clauses and comparisons are research inputs, not verified legal instruments. Claims
about other projects, future enforceability and insolvency outcomes are not adopted
merely because both reports repeat them.

## Selected ownership and licensing model

1. **Community licence:** the complete official Core remains AGPL-3.0-or-later.
   Lawful commercial use does not require a donation or alternative licence.
   Existing recipients keep their existing licence rights, subject to its terms.
2. **New accepted Core:** seek transfer of the transferable copyright actually held
   by the contributing rights holder to a legally identified Qualified DAIA Foundation.
   This is the selected end state, not a statement that submitting or merging a PR
   transfers ownership. Moral rights, patents and third-party permissions need separate
   treatment; an assignment cannot create copyright in unprotected generated material.
3. **Existing work:** the founder retains rights actually held pending a separate
   founder-to-foundation instrument. Existing contributions are not retroactively
   assigned. Audit original, employer, jointly owned, generated and incorporated work.
   An adequate supplemental licence may clear a specifically documented legacy
   exception; it must not be labelled foundation ownership.
4. **Official alternative licensing:** only the independent foundation may issue it,
   and only for a release with a verified chain of sufficient rights. Ownership of
   some files is not clearance of the whole release or its dependencies.
5. **AGPL continuity:** the same project-controlled Core offered commercially must
   remain available under AGPL. Put this obligation into the final instruments and
   succession rules. Do not claim a policy alone guarantees perpetual hosting.
6. **Compensation:** project income supports DAIA. A salary or maintainer fee for
   the founder or another worker requires the independent foundation to request
   the work and approve its agreement and budget through non-conflicted decision-makers.
   There is no personal royalty, fixed revenue share or current payment authorization.

This direction supersedes the retained-copyright supplemental-grant default in
this policy branch. Earlier grant drafts remain documented alternatives, not
execution-ready forms for the selected model.

## What counts as Core, and when rights are recorded

A future agreement must identify the legal contributor or authorized employer,
its version, covered submission channels and a versioned Core scope. It should
cover identifiable future contributions made through authorized workers, subject
to legal validation of the transfer mechanism. A worker key proves an actor's
identity; it cannot sign away an employer's rights by itself.

For each accepted contribution, record the exact patch/blob hashes, agreement
reference, authority, exclusions and acceptance event. Distinguish permission to
receive and review a proposal from transfer of an accepted contribution. A rejected
patch, unrelated customer job, research for another project, private software or
external repository does not become DAIA property. Reuse for Core requires a
separate eligible submission. Third-party components retain their own terms.

## Transition before a foundation exists

The desired interim path remains part of the design: the founder may administer
rights under a specifically reviewed instrument with a duty to transfer them to
the qualified foundation. It must not permit personal customer licensing, sale,
pledge or private appropriation of the aggregated rights. Calling someone a
custodian does not isolate assets from death, incapacity or insolvency.

**Do not activate that path with the current drafts.** Counsel must resolve the
actual recipient, assignment formalities, future-work identification, succession,
enforcement, participant remedies and a concrete transfer trigger and deadline.
No arbitrary deadline in either report is silently adopted. If a workable interim
instrument cannot be established, form the foundation before accepting external
copyright-relevant Core under the ownership programme.

Until one of those routes is executed, existing AGPL development continues and
research/proposals may be reviewed. Do not merge new external copyright-relevant
Core as ownership-cleared work. A specifically approved AGPL-only exception must
be recorded as such and excluded from proprietary clearance unless adequate rights
are obtained later. Existing AGPL rights are not revoked by this administrative rule.

## Implementation milestones and acceptance evidence

These are open work items, not implemented legal or technical controls.

| ID | Action | Completion evidence |
| --- | --- | --- |
| RIGHTS-01 | Specify Core scope, submission channels and acceptance semantics | Versioned scope; included/excluded examples; no automatic capture of external jobs |
| RIGHTS-02 | Obtain review of individual/corporate assignment instruments and, if used, interim transfer structure | Actual legal parties and signing authority; reviewed deed/signature workflow; future-work, patent, moral-right and employer treatment; enforceable trigger/succession plan |
| RIGHTS-03 | Establish qualified foundation and founder instrument when authorized | Formation documents; independent board and conflicts rules; sufficient founder rights; no invented present ownership |
| RIGHTS-04 | Implement private assent and provenance register | Agreement version and artifact-bound evidence; no names/signatures in public Git; authorized worker mapping and revocation behaviour |
| RIGHTS-05 | Enforce contribution clearance before Core acceptance | Demonstrate missing agreement, employer authority or excluded scope cannot be marked ownership-cleared; exceptions remain visibly AGPL-only |
| RIGHTS-06 | Audit existing Core and dependencies | Exact release manifest; each component assigned, otherwise licensed, excluded or unresolved; imported research also recorded without presuming exclusive ownership |
| RIGHTS-07 | Enable foundation commercial programme only after clearance | Approved exact release, AGPL counterpart, qualified signatory, customer terms and lawful accounting; compensation decisions separate |

For foundation qualification, use at least three board members with a majority
independent of the founder as the design requirement, with purpose-bound income,
conflict recusals, no unilateral founder control, and transfer on dissolution only
to a qualified nonprofit successor. These requirements still need legal embodiment;
this document creates no entity, board appointment or financial commitment.

## Verification and limits

The Dutch amendment and commencement were checked against primary publications.
The [GNU copyright-assignment guidance](https://www.gnu.org/licenses/why-assign.html)
illustrates centralized enforcement; [GNU maintainer guidance](https://www.gnu.org/prep/maintain/html_node/Copyright-Papers.html)
discusses assignments covering future changes. Neither validates a Dutch DAIA deed.
The [Qt contribution agreement](https://www.qt.io/community/legal-contribution-agreement-qt)
illustrates the alternative of retained ownership with broad licensing rights;
DAIA has not adopted it. Read the [actual AGPL text](../LICENSE), particularly
sections 2, 10 and 13, for existing public licence rights and obligations.

Publishing these anonymized reports is authorized research publication, not an
assertion that their entire contents are copyright-assignable or proprietary-cleared.
No agreement was signed, no retrospective consent was invented, no contributor
identity was published, and no external legal adviser was contacted by this change.
