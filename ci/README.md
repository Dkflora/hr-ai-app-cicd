# What these Python files do

Students do not need to write every helper from scratch. The repository provides application setup and deployment helpers. In class, we connect them through GitHub Actions and explain their inputs, results and release decisions.

## Read the pipeline in this order

1. `release.py`: check the prompt format, publish its numbered Langfuse version, and package Python with that exact prompt.
2. `deploy_candidate.py`: put that package into the staging Lambda version.
3. `evaluate_api.py`: sign in as synthetic employees, ask the real application the test questions, and check its answers.
4. `report.py`: explain what passed and what failed. Failed or missing required results block release.
5. `promote_lab.py`: move the classroom approved pointer only when the tested release passes.

## Four views of application quality

- `prepare_promptfoo.py` and `check_promptfoo.py`: check required facts, forbidden facts and sources in the captured answers.
- `langfuse_experiment.py`: put those questions, captured answers and scores into a Langfuse experiment for comparison.
- `deepeval_check.py`: have another model judge approved reference outcomes, including correct access refusals. It can disagree with other checks and needs review.
- `evidently_drift.py`: compare answer length and latency between two runs. A change is a reason to investigate, not proof of a bad answer.

## Prepared automation

`deploy_frontend.py` uploads the React files already produced by npm run build to S3, then refreshes CloudFront. It is a deployment helper, not an AI evaluation.

`auth.py` gets fresh test-user tokens without printing passwords. `rollback_lab.py` restores a previous classroom release pointer. `tests/` checks the prompt, release packaging, judge behavior and tracing.

## Explain the grader itself

`judge_agreement.py` compares human and model grades on the same cases. `compare_versions.py` compares baseline and candidate cases with repeated runs and an illustrative uncertainty calculation. We explain the results; students do not need to derive the statistical formulas or rewrite the provider adapter during this four-hour lab.

A file is not proof that an integration passed. Refer to the instructor rehearsal status for what has actually run.
