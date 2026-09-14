# DAIA rights model v2: retained copyright, entity-neutral licensing

**Selected design, confirmed by the owner on 14 September 2026; not an operative
agreement. No licence programme, contributor
assent, legal entity or commercial clearance is activated by this change.**
The owner selected retained contributor copyright and company licensing. This
design supersedes mandatory foundation ownership in the
[earlier decision](core-rights-decision-2026-09-13.md). `LICENSE` is unchanged.

See the [maintainer assessment and implementation evidence](research/licensing-model-v2-assessment-2026-09-14.md).

## Assessment of PR #21 and the retained-copyright proposal

Reviewed baseline: PR #21 at `840298b5d4e3d6ce0279e10328e7b06f00170057`.
The PR deliberately chose assignment to meet a central-ownership objective; it did
not establish that assignment was necessary for dual licensing. Its AGPL/alternative
licence distinction, caution about AI ownership, separate legal participant and
worker, private rights register, and warning against imaginary interim custody
are worth keeping. The correction about Dutch law effective 1 January 2026 is also
correct: the agreement for transfer or exclusive licensing must be written; delivery
of an assignment still requires a deed. A nonexclusive grant is a different route.
See sources [1]-[3].

**Recommendation:** individual and organizational contributors retain their rights
and use the same bounded supplemental licence. Assignment or an exclusive licence
may be negotiated separately for exceptional components, never inferred from their
importance or introduced through a changed website. A nonexclusive grant can supply
the intended commercial permissions without later relicensing consent. It is not
identical to ownership: standing to sue, mandatory author protections, insolvency,
and defective rights chains still require analysis. Neither model repairs a grant
from the wrong employer, copied code, or noncopyrightable output.

The proposed participant/worker separation and acceptance trigger are useful, with
three corrections: permission must predate the relevant Core work; a maintainer
cannot retrospectively relabel an external job; and a merge or hash does not itself
prove legal authority. An artifact manifest is evidence infrastructure, not proof
of originality, a substitute for counsel, or protection against governance capture.

Qt illustrates contributor ownership with grants to a commercial company [4]. It
does not validate DAIA's Dutch instrument. Calling the grant 'commercially
interoperable' is too vague: contributors must expressly understand proprietary
sublicensing and, in the company route, potential shareholder benefit.

## Recommended parties and rights

```text
Human / organization (actual rights holder)
  | signed admission agreement + finite worker authorization
  | retains copyright; AGPL permission to everyone
  v
Authorized worker -- no legal assent power
  |-- preclassified EXTERNAL JOB --> customer's/project's own terms
  |                                 no DAIA Core rights claim
  `-- preclassified CORE --> submission --> rights review --> recorded acceptance
                                                           + official inclusion
                                                              |
                                                   supplemental grant attaches
                                                              v
                                         Identified existing DAIA Licensor
                                         (company OR optional foundation)
                                             |                   |
                                       complete AGPL Core    commercial customers
                                                            private changes allowed
```

'Only official licensor' concerns the official DAIA programme, not a monopoly over
contributors' own work, independent implementations or lawful AGPL forks. The
founder is not personally licensed to relicense other contributors' work merely
because they own shares in the licensor.

## Company is permitted; neutrality is not implied

The preferred first recipient is an **existing, identified legal entity**. A
founder-owned company may qualify; a foundation and independent nonprofit board
are not mandatory. No company is asserted to exist or appointed here. A trade name,
repository organization, prospective company or sole proprietorship must not be
misrepresented as a separate incorporated legal person.

The signed schedule must disclose the exact counterparty, jurisdiction, registration,
address, signatory authority, founder control and commercial purpose to contributors.
Private identities need not be committed to public Git, but the counterparty cannot
be hidden from someone signing with it. Private evidence must be available to
qualified due-diligence reviewers under appropriate confidentiality controls.

A company may earn profit and, subject to applicable law, pay for work and make
shareholder distributions [7]. That is **not** the earlier project-only nonprofit
bargain. The agreement must say so plainly before assent. No payout, revenue share,
salary or funding commitment is authorized here. Compensation needs lawful corporate
approvals, documented work and conflict handling; tax, employment and distribution
rules need professional review. Existing restricted donations, host terms and signed
foundation-only grants remain restricted. A later policy edit cannot convert them.
A genuine foundation route may separately retain project-only spending, an independent
board, no self-approved compensation and nonprofit dissolution requirements.

## Non-negotiable open-Core obligations

Every accepted covered contribution and every licensor-owned or licensor-controlled
Core improvement included in an official release, official hosted Core service or
commercial Core deliverable must have complete corresponding source publicly
available under AGPL-3.0-or-later no later than that release/use. Include required
build material and notices, without publishing customer data or secrets. No permanent
superior closed official Core branch, rebranding as 'enterprise', transfer to an
affiliate or removal from a scope list may evade this obligation. This does not
require publication of unused experiments or compel future development.

Customers' own changes and independently licensed external job outputs do not
become Core through this agreement. Customer contracts must distinguish customer-owned
work from licensor-controlled Core work before commissioning it. Do not accept a
customer's confidentiality terms over official Core that must be published; do not
promise to open customer-owned work without their permission. A derivative or
dependency which cannot lawfully be supplied under both required arrangements must
be excluded, replaced lawfully or separately cleared, not papered over.

Put the guarantee into each executed grant, the licensor's acceptance, founder and
staff/contractor instruments where needed, successor instruments and release policy.
It is not an extra restriction added to AGPL. Existing AGPL permissions continue
under their own conditions [3]. Publish source to an independently recoverable
mirror; a contract cannot guarantee a host or solvent operator forever.

## Succession, sale and failure

Preauthorize only transfer of the entire relevant contractual position to a
Qualified Successor which is an existing legal entity, has authority and operational
capacity, accepts every applicable contributor obligation in writing, preserves
records, honours existing customer grants, and preserves the same AGPL guarantee.
A company or foundation can qualify under **new v2 instruments**. Make successor
acceptance enforceable by contributors, not merely a private promise to the seller.
No sale of a detached, unrestricted relicensing permission; no pledge granting a
creditor broader exploitation rights; no automatic parallel authority for the former
licensor. Customer sublicensing is expressly distinct from succession.

An asset transfer needs the appropriate legal acts; Dutch contract transfer under
BW 6:159 is not achieved by a changelog. Counsel must settle advance cooperation,
notice, accession and assignment of associated claims. A share sale normally leaves
the contracting entity in place: bind that entity continuously and require notice
of control changes, not a fictional 'new grant'. Do not make ordinary customers'
existing licences contingent on shareholder identity. Mandatory insolvency law may
limit contractual restrictions: no bankruptcy-remoteness guarantee is made.

Before dissolution seek a qualified successor and secure source/evidence archives.
If none accepts, stop new alternative licensing; preserve public AGPL access and
already valid customer permissions within their existing scope. The founder or an
estate does not receive a discretionary commercial fallback. The default entity-first
route avoids personal custody, but not the entity's own insolvency risk. See the
[interim analysis](interim-rights-custody-proposal.md).

## Minimum acceptance state and implementation status

The [grant architecture](contributor-commercial-grant.md) and
[private register/acceptance workflow](licensing-rights-register.md) specify the
instruments and evidence. They are not deployed services.

| Gate | Evidence needed before activation | Status in this change |
| --- | --- | --- |
| RIGHTS-01 | Versioned Core scope, pre-job classification, acceptance/revocation semantics | Specified in draft; runtime integration not implemented |
| RIGHTS-02 | Reviewed individual/organizational agreements, actual parties and signatures | Open; no executed agreement |
| RIGHTS-03 | Existing licensor, authority, founder/staff rights and successor instruments | Open; no entity or title asserted |
| RIGHTS-04 | Private identity, employer authority, worker mappings, immutable acceptance records | Data/flow design only; no identity service |
| RIGHTS-05 | Merge-control and recovery tests under existing maintainer/security rules | Planned; offline manifest checker is not this gate |
| RIGHTS-06 | Full legacy/dependency/build audit and independent inventory | Open; no release commercially cleared |
| RIGHTS-07 | Signed release authorization, public AGPL counterpart, reviewed customer/tax terms | Open; preview `--release` deliberately refuses |

The repository may remain public AGPL. Issues and research may be discussed, but
tests, documentation, snippets and patches can also contain protectable expression.
Do not silently integrate uncleared external expression into the dual-licensable
Core. Until actual agreements and enforcement exist, hold such PRs or explicitly
approve and record an AGPL-only exception. The exception is lawful AGPL work, not
commercial clearance, and may need exclusion or a separate grant later. This
administrative proposal does not narrow anyone's existing AGPL permissions.

## Bounded provenance observations, not an ownership audit

This review examined the pinned PR policy files and repository tree. It did not
complete a full historical or private-contract audit. The owner's statement of no
known external substantive human contribution is not proof of a clean title chain.
The earlier register's three Git author identities are not three proven owners.
AI authors/committers and service accounts must not be treated as legal grantors.

Before any alternative release review at least original `src/daia` code, tests and
fixtures, `scripts`, deployment/container material, website code and assets, generated
files, lockfile-selected and bundled dependencies, and copied documentation/research.
The two archived reports remain research with stated source limitations; publication
is not proof of exclusive authorship or proprietary clearance. Maintain all prior
contributors to surviving material, not merely each file's last author. A new AI-assisted
commit, including this change, is not itself a founder ownership certificate.

## Mandatory Dutch counsel review

Validate the actual nonexclusive future-contribution grant, scope and finite
participation windows against determinability and Auteurswet 25b-25h, including
25f's future-work protection [5]. Determine applicable remuneration, transparency,
termination and mandatory-law treatment for code versus other works; do not assume
'royalty-free', 'perpetual' or a foreign choice of law waives these rights.
Validate electronic assent and organizational authority; employer/contractor/joint
rights internationally; minors and moral rights; patent sublicensing and defence;
independent enforcement standing and authority surviving death or incapacity;
6:159 successor cooperation and any third-party stipulations; insolvency and
customer-survival provisions; GDPR purpose, access and defensible retention periods;
and the actual commercial, founder, corporate-conflict and tax instruments.

The proposed 12-month authorization window and 60-day cure period in the draft
are reviewable design choices, not statutory safe harbours. No contract is presented
for signature until these points have concrete answers and the documents agree.

## Primary sources and what they establish

1. [Staatsblad 2025, 352, Article I.A](https://zoek.officielebekendmakingen.nl/stb-2025-352.html): amended written agreement and assignment-delivery formalities; not validation of this draft.
2. [Staatsblad 2025, 392](https://zoek.officielebekendmakingen.nl/stb-2025-392.html): commencement on 1 January 2026.
3. [Official GNU AGPLv3](https://www.gnu.org/licenses/agpl-3.0.dbk), especially sections 2, 5, 8, 10, 11 and 13: public permissions, conditions and downstream rights; separate proprietary authority is not supplied by AGPL alone.
4. [Qt contributor agreement guidance](https://www.qt.io/community/legal-contribution-agreement-qt): actual retained-ownership/company precedent; not a Dutch DAIA legal opinion.
5. [Staatsblad 2015, 257](https://zoek.officielebekendmakingen.nl/stb-2015-257.html) and [official explanation of future-work terms](https://zoek.officielebekendmakingen.nl/kst-33308-C.html): author-contract protections and contextual reasonableness; read with subsequent amendments, not as a complete current consolidation.
6. [Apache contributor-agreement guidance](https://www.apache.org/licenses/contributor-agreements.html) and [Apache-2.0 sections 2-3](https://www.apache.org/licenses/LICENSE-2.0): organizational assent practice and a bounded copyright/patent model; neither is adopted as DAIA's agreement.
7. [KVK: sole proprietorship versus BV](https://www.kvk.nl/starten/een-eenmanszaak-of-bv-als-rechtsvorm-kiezen/): legal-entity and profit/compensation context; no DAIA tax conclusion.

The proposed clauses, numerical periods, successor criteria and engineering design
above are recommendations, not propositions that these sources guarantee them.
