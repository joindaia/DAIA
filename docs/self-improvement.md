# DAIA improving DAIA

The platform is an eligible project, not a privileged agent. Contributors must explicitly consent to platform-improvement work. Such consent and workload dispatch are planned; the current demo only implements certificate work.

## Improvement contract

Before assigning a proposal, the maintainer freezes an input commit, precise objective, non-goals, benchmark revision, evaluator digest, acceptance threshold, resource budget, risk class and promotion policy. Unmeasured baseline values must be marked unknown, not fabricated. The producer cannot write evaluator fixtures, scoring code, credentials, permissions or its own approval policy through the same job.

A proposal returns a patch plus reproducibility instructions and evidence. Independently assigned contributors reproduce measurements and challenge regressions. A trusted runner executes tests; a maintainer reviews the exact resulting commit. In v0 **every repository merge remains human-controlled**, including documentation and test changes. Tests can weaken security too.

## Evaluation discipline

Use public training fixtures for exploration and held-out evaluation for acceptance. Keep the evaluation environment outside candidate-controlled code. Compare useful validated outcomes per fixed workload budget, including review cost, retries, failure rates and variance. Do not optimize raw job completion counts or unverifiable self-reported token savings. An improvement on one seed is not reliable evidence of general benefit.

Preserve unsuccessful variants and measurements in a bounded private archive. A candidate that is not the current winner may inform later approaches. Do not imply that every candidate must improve production immediately.

## Protected changes

Authentication, signing, contributor-root mapping, assignment eligibility, review policy, evaluator code, CI permissions, secrets, sandbox boundaries, deployment approval and governance are protected. Changes to these controls are evaluated under the previously approved policy and require distinct authorized human approval. Neither an agent quorum nor a benchmark victory can authorize a new authority level.

No agent holds production deployment credentials. No agent can change branch protection. No release runs merely because the result state becomes promoted. Add canary and rollback procedures before any later deployment automation.

## First useful internal job

Start with a bounded, low-privilege improvement such as adding a regression fixture for a lease race, improving documentation from a failing integration test, or optimizing a read-only queue query while preserving behavior. Do not make "rewrite your own scheduler and deploy it" the first trial.

The sample at `examples/platform-improvement-job.json` is a contract template, not an executable job or a claimed benchmark result.
