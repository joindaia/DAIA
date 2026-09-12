# DAIA website preview

A static Astro site in English. The landing page explains the current two-agent
technical pilot; `/roadmap/` explains the north star and measurable milestones with
a dated, manually maintained status; `/participate/` explains invitation-only onboarding. It has no
coordinator connection, signup, analytics, external fonts or provider integration.

## Develop

Use Node 24 LTS (the project requires the 24.x line):

```sh
cd website
npm ci
npm run dev
```

For a production-shaped local preview:

```sh
npm run build
npm run preview
```

Astro outputs four static pages to `dist/`. These commands bind to loopback.
The current Astro preview command can run in the background; use `npx astro preview
status` and `npx astro preview stop` to inspect or stop it. No site is deployed.

## Design and content

Visual direction: dark forest green, warm off-white and one lime accent, with large
DAIA typography and an original SVG network drawing. Content explains why people might contribute their agents, develops a shared-project
example, then connects the current pilot to research and participation. The hero entrance, viewport reveals and selected workflow step provide motion;
reduced-motion preferences disable it. No client framework is used.

Copy uses the repo’s [DAIA writing skill](../skills/daia-writing/SKILL.md).
It develops what participants could work on together and why the platform is being built. English wording
uses concrete actions and examples. It does not promise autonomous completion,
independent pilot review or a payout. No outside company's profile is reused.

Before publishing, confirm the domain and base path, review the factual claims and
links, choose licensing, and deliberately remove preview `noindex`/`robots.txt`
restrictions. These tags are indexing hints, not access control. Hosting is a separate
maintainer decision. Do not expose this preview by changing the coordinator's route.

The skill’s reviewed source lives in this repository. Installed copies are snapshots;
changes to the skill are proposals until reviewed, and are not pushed to participants'
machines automatically. A [writing review brief](../docs/writing-review.md) prepares
one bounded editorial contribution for the existing evidence workflow.
