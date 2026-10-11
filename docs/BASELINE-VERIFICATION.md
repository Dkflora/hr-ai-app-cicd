# Verified HR classroom baseline

- Instructor repository: https://github.com/kserge2001/hr-rag-evaluation-instructor (private).
- Working implementation commit: `af0fa05a42534ae63d8b494d6414d48e1d735249`.
- Successful hosted run: https://github.com/kserge2001/hr-rag-evaluation-instructor/actions/runs/38120701358.
- 43/43 cases passed every repetition; 86 authenticated application requests recorded. Release gate PASS.
- Prompt version 8; candidate Lambda version 11. Exact artifact, dataset and prompt digests are retained in the run's release manifest.
- Static/build checks, API evaluation, official Langfuse and Promptfoo Actions, prepared DeepEval grading, Evidently report, exact-version classroom promotion and production demonstration succeeded.
- Earlier failing run: https://github.com/kserge2001/hr-rag-evaluation-instructor/actions/runs/38119603482. It shows the gate blocking promotion before the retrieval fixes.
- Eighteen local CI tests pass. CloudFront routing update deployed. AWS resources remain running.

## Boundaries

This is a synthetic classroom baseline, not evidence of zero production errors or a security certification. Future model runs can vary. The production job makes no production changes. GitHub environment approvals and protected-branch review policy must be configured for the class's reviewer arrangement; a completed demonstration job does not prove human approval occurred. The successful run verifies the main path; branch/PR triggers use static checks and no candidate deployment. Drift uses numeric proxies and a captured failing classroom reference, not a stable production baseline. Human grader agreement requires independent human labels.
