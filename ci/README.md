# How the pipeline helpers fit together

The helpers are provided. We connect them through GitHub Actions, configure the test cases and release rules, and interpret the results. We do not need to write every helper from scratch.

## Main delivery path

| Stage | Prepared helper | What we verify |
|---|---|---|
| Package | `release.py` | Prompt format, numbered Langfuse version and exact release identity |
| Deploy candidate | `deploy_candidate.py` | The intended package reaches the staging Lambda version |
| Evaluate API | `evaluate_api.py` | Authenticated test users receive correct, authorized answers |
| Report | `report.py` | All required cases completed and the results are recorded |
| Approve release | `promote_lab.py` | Only the exact passing release moves the approved staging pointer |

## Four views of answer quality

- Promptfoo checks required facts, prohibited facts and sources in the captured API answers.
- Langfuse records the dataset experiment and scores by release so we can compare results.
- DeepEval grades the answer against approved reference outcomes; disagreements need review.
- Evidently compares numeric answer-length and latency patterns. A shift prompts investigation, not an automatic verdict that an answer is wrong.

The prepared adapters connect these tools to the same captured API results. We configure their workflow blocks rather than rewrite the adapters.

## Supporting automation

`auth.py` is used internally by the API evaluator. It reads dedicated test credentials from Secrets Manager, signs in through Cognito and obtains fresh tokens. This runs on each evaluation; creating the users during setup does not supply permanent tokens.

`deploy_frontend.py` uploads the built React files to S3 and refreshes CloudFront. `rollback_lab.py` restores a previous approved pointer within staging. `tests/` verifies prompt structure, release packaging, judge behavior and trace handling.

## Compare releases and review the grader

`compare_versions.py` compares the same cases across baseline and candidate runs, including repeated generations and an illustrative uncertainty calculation. `judge_agreement.py` compares independent human grades with model grades. We interpret these reports and explain disagreements; their statistical and provider implementations are already supplied.

A script existing in the repository does not prove a successful run. Use our own workflow results, traces and release records as evidence.
