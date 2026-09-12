# GitHub contribution workflow

This repository uses a bounded, maintainer-led contribution workflow. GitHub Actions checks the
reference implementation on Ubuntu and Windows and builds the static website on Ubuntu with
Node 24. The workflow has read-only repository permissions, no secrets, deployment, automatic
merge, `pull_request_target` trigger or self-hosted runner. It may also be run manually with
**Run workflow**.

## Propose bounded work

Open a reproducible bug or a bounded development task. Include a baseline, in-scope and
out-of-scope work, observable acceptance criteria, and the smallest evidence plan. Do not use an
issue to combine a redesign, a policy change and an unrelated repair.

Choose one contribution type:

- **Source analysis** supplies a frozen, bounded finding and supporting references. Submitted
  analysis and patches remain inert until a maintainer triages them; contributed executable code
  is not admitted through this path.
- **Trusted local code change** is implemented and tested by a maintainer or trusted local
  contributor. Its pull request links the issue, reports commands that actually ran, and records
  untested environments or limits.

The opt-in two-agent technical pilot can provide shared-ownership technical feedback for eligible
source-evidence campaigns. It is not independent review, merge approval, or evidence that a
change is safe to deploy. Follow the protocol and pilot documents for its frozen-policy limits.

## Review and merge

The pull-request template requires the issue, acceptance criteria, relevant evidence, privacy
considerations and protected-boundary impact. Passing CI and agent reviews inform a decision; they
do not make it. The maintainer verifies the stated criteria before changing scope, requesting
revisions or merging. The owner has authorized routine DAIA integration through the
[standing delegation](maintainer-delegation.md); assigned workers cannot approve or
merge their own submissions.

The repository does not claim enforcement through premium GitHub branch protection. If repository
settings later make checks required, configure them deliberately and retain the separate
maintainer integration decision.
Dependabot opens reviewable updates for GitHub Actions and the website npm dependencies; it cannot merge them.

## Local checks

Run the applicable checks before opening a pull request. Reference-code changes normally run
`python -m pytest -q`, `python -m daia.cli demo`, and the privacy guard described in
[CONTRIBUTING.md](../CONTRIBUTING.md). Website changes run `npm ci` and `npm run build` from
`website/`. Report actual results and do not represent unrun host, CI or pilot checks as complete.
