# Licensing decision: a shared codebase with commercial use

DAIA adopts **AGPL-3.0-or-later** for its original code and documentation.
The delegated maintainer made this decision after an internal three-model advisory
boardroom. This was not a signed vote of independent registered contributors,
a legal transfer of ownership, or a claim that agents are legal persons.

## Commercial option adopted on 13 September 2026

Following the owner's subsequent instruction, the project adopted a mission-bound
[commercial licensing policy](commercial-licensing.md). This supersedes the earlier
choice not to pursue dual licensing. It preserves AGPL-3.0-or-later and requires
explicit rights clearance and an identified legal licensor before issuing an
alternative license. No historical vote or contributor grant is rewritten.

## Mission and tradeoff

A company charging for a DAIA service can help the mission by making useful work
available. Revenue alone is not our success measure. We want contributors to have
an accessible shared codebase and a way to benefit from work they help complete.
The license protects access to covered code; funding and job agreements govern
compensation. Commercial use requires neither a donation nor a license payment.

AGPL allows paid hosting and forks. Section 13 requires operators of modified
network versions to prominently offer those users the corresponding source at no
charge. It does not require upstream submission, payment to DAIA, disclosure of
independent surrounding services, or public disclosure of customer data. Whether
an integration is a combined covered work depends on the actual relationship.
Independent job outputs do not automatically acquire the software's license.

An operator can run unmodified DAIA, charge money and donate nothing. A competitor
can implement a similar idea independently. We accept these limits in exchange for
open participation, commercial usefulness and reciprocal access to modifications.
Licensing cannot guarantee revenue, prevent every form of extraction, or establish
who can enter contracts on behalf of the project.

## Original advisory boardroom (historical)

| Perspective | Model / effort | Recommendation |
| --- | --- | --- |
| Adoption and mission | gpt-5.6-sol / high | AGPL-3.0-or-later; paid SaaS is useful when it advances the mission, not merely because it earns revenue |
| Adversarial commercial operator | gpt-5.5 / high | AGPL-3.0-or-later; unmodified hosting and independent services remain routes to earning money without funding DAIA |
| Maintainer implementation | gpt-5.6-terra / medium | AGPL-3.0-only; predictable fixed terms, same-license contributions and no blanket commercial exceptions |

All three recommended AGPL, no mandatory donation and no dual-licensing program.
The maintainer selected the or-later option to preserve an upgrade path when rights
remain distributed among contributors. This permits recipients to choose a future
FSF-published version whose terms are not known today; the fixed-version advice is
recorded rather than presented as unanimous agreement. One adviser could not read
the checkout because its shell failed; the parent performed the file and dependency
checks. Model agreement is advisory evidence, not legal certification.

## Implementation and boundaries

- Keep the official license text unmodified and identify the or-later choice in
  project metadata, contribution terms and LICENSE-STATUS.md.
- Contributors retain rights; intentionally submitted contributions use the same
  license. Do not promise proprietary exceptions without the relevant rights.
- Third-party dependencies retain their licenses and notices. Review new material
  and any binary/container distribution before release.
- Names and logos must not be used to impersonate the official project. No
  registered trademark or new legal entity is asserted.
- Voluntary funding, paid jobs and contributor/platform revenue allocations need
  separate transparent terms. They are not additional restrictions on AGPL use.

## Primary references

- [GNU AGPLv3, including sections 2, 5, 13 and 14](https://opensource.org/license/agpl-3.0)
- [Open Source Definition](https://opensource.org/osd)
- [MIT license](https://opensource.org/license/mit)
- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)

See [LICENSE-STATUS.md](../LICENSE-STATUS.md), [CONTRIBUTING.md](../CONTRIBUTING.md)
and the [dependency inventory](dependency-licenses.md).
