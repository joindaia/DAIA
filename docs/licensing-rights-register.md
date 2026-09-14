# Rights register and release clearance

**Design only. No executed grant or commercial clearance is recorded by this change.**
Use the [current model](licensing-model-v2.md), not the superseded assignment default.
Public Git metadata, model output claims, signed worker messages and green CI are
not ownership certificates. The licensor can be a company or optional foundation;
the actual counterparty and signatory authority must be established first.

## Private authoritative records

Maintain an access-controlled, backed-up, append-only evidence store separate from
worker jobs and the public repository. Specify GDPR controller, purposes, legal
basis, retention review, access/deletion handling and lawful successor transfer.
Rights evidence may need long retention; do not assume either immediate erasure
or unlimited retention is always lawful. Do not collect provider tokens or publish
hashes of names/emails. Use random opaque references, not identity-derived hashes.

Record legal party/capacity, counterparty, agreement bytes/version/hash and assent
receipt; organizational/employer/contractor/joint authority; versioned scope and
finite participation interval; participant-to-worker authorization/revocation;
pre-dispatch Core classification; base/patch/content hashes; submission/withdrawal;
accepted inclusion and authorized maintainer identity; exclusions and provenance;
patent position; successor chain; and the reviewer/evidence for clearance decisions.
Record actual event times separately from later evidence ingestion, never backdate.
An enforcement mandate and founder/legacy schedule are distinct from future grants.

Retain all rightsholders and inherited material in an artifact's history, including
cherry-picks, squashes, renames and copied hunks. One file/last-author/one-CLA mapping
is not sufficient. The rights-map reference must point to that complete assessment.

## Public projection

Publish only reviewed artifact references and opaque evidence references. States:

| State | Meaning |
| --- | --- |
| `cleared` | Named qualified reviewer has verified sufficient original-Core commercial rights, with private evidence; not ownership by DAIA |
| `agpl-only` | Adequate public AGPL route; no adequate supplemental authority |
| `unverified` | Insufficient evidence; do not infer either permission or infringement |
| `third-party` | Supplied under its own documented terms; assess compatibility/notices separately |
| `excluded` | Not included in the proposed release; do not hide included bytes using this label |

These are claims supported by evidence, not self-service participant assertions.
Completely anonymous original contributions must not be marked commercially cleared
merely on a worker's declaration. Adequate independently established permissions
for third-party material are a different route and require a documented review.

## Admission and GitHub workflow

1. Present named counterparty, immutable agreement/scope, company-profit disclosure
   and readable summary to the human/organizational signer. Obtain explicit e-sign
   assent through a private flow and give them a durable copy. Check organizational
   signatory/employee authority before clearance. A DCO, ordinary PR checkbox or
   worker signature alone is not this agreement.
2. Bind the public account to that private record using an authenticated, expiring
   challenge. Bind authorized workers separately. A CLA bot reports an opaque result;
   it is neither the contract nor proof that the signer owns every contribution.
3. Before Core work, freeze job class/scope/terms and worker authorization. External
   jobs use their own terms. Recheck expiry, revocation and employer changes before
   acceptance; do not let a stale webhook or changed PR reuse prior clearance.
4. Review exact material and full inherited rights map. Bind preclearance to the
   final content digest, not a mutable branch label. A different base, rebase with
   changed content or integration edit requires reconciliation. Record exclusions.
5. An authorized maintainer alone performs acceptance under the existing security
   and merge policy. Match actual inclusion to the approved content; append the
   evidence receipt. A crash, missing receipt or bypassed merge remains unresolved
   for commercial release until independently reconciled. No retroactive assent.
6. Independently inventory the actual release: sources, generated outputs, bundled
   dependencies, containers, website assets and notices. Reconcile every included
   artifact against the rights map. Strong copyleft/public-only dependencies cannot
   be erased by the proprietary contract; obtain appropriate permission or change
   the package. Publish the matching complete AGPL Core source before release.
7. Have an authorized reviewer approve the exact manifest and legal signatory issue
   the reviewed customer licence. Store tamper-evident release authorization outside
   contributor-controlled changes; rotate/back up access without changing grants.

The private assent store, authenticated reviewer attestations, merge enforcement,
independent inventory producer and production release authorization are **not
implemented** by this PR. No live admission or security gate is weakened.

## Offline consistency preview

`scripts/check_licensing_manifest.py` checks a public projection against a separately
supplied inventory. It checks exact artifact coverage/digests, opaque evidence
references, an identical AGPL source-commit reference, scope/repository identity,
unknown/private field rejection, duplicate keys/paths and unresolved Core states.
It checks only the shape of a licence label, not membership in the SPDX registry
or legal compatibility. A syntactically plausible invented label can pass. The
path filter is not a complete privacy scanner. It cannot authenticate the referenced evidence, prove copyright, confirm public
source availability, reconstruct lineage or judge a third-party licence's compatibility.
A third-party record and a `cleared` label still need the underlying legal review.

Inventory format: a nonempty JSON array of `{path, sha256}` for every artifact in
the actual proposed package, prepared independently of its rights manifest. The checker never reads the release
tree; if both supplied descriptions omit a file or remain stale, it cannot detect
that fact. The `daia-core-v2` identifier alone activates no agreement or scope.
Manifest fields are `schema: daia-rights-preview-v1`, `scope: daia-core-v2`, integer
`repository_id: 1367256015`, `source_commit`, equal `agpl_source_commit`,
`inventory_sha256`, `licensor_ref` and `records`. Commit IDs are 40 lowercase hex;
artifact/inventory digests are SHA-256. The inventory digest hashes compact,
key-sorted ASCII JSON of the entries sorted by path. Evidence references match
`ref_` followed by 32 random lowercase hexadecimal digits; the store authenticates
them, the preview only checks syntax.

Every record has `path`, `sha256`, `category`, `status`, `rights_map_ref`.
Core records additionally have `grant_ref`, `acceptance_ref`, `patent_ref`.
Third-party records instead have `license_id` (one SPDX ID or reviewed LicenseRef),
`review_ref`, `notices_ref`, and retain `status: third-party`. An original-Core
record is structurally complete only at `status: cleared`. For multiple licences
use a reviewed LicenseRef and retain the full expression privately/in the notices.
No synthetic real-world clearance entries are shipped; tests use synthetic data.

```sh
python scripts/check_licensing_manifest.py manifest.json inventory.json
python scripts/check_licensing_manifest.py manifest.json inventory.json --release
python -m unittest discover -s tests -p 'test_licensing_manifest.py'
```

Normal exit 0 means consistency only; invalid input exits 1. `--release` always
exits 2: no production authority has been implemented. JSON output always includes
`commercial_release_authorized: false`. Editing `licensing/program.json` cannot
activate an agreement or turn this preview into a production release gate.
