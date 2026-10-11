# HR RAG lab: evaluate and release an application change

Duration: four hours. The Kubernetes lab already taught manual tracing and the Langfuse UI judge. This lab inherits the application and automates the earlier RAG setup.

## What students inherit
React frontend, Python Lambdas, Cognito identities, row-level security, document access filtering, Bedrock Guardrails, Terraform, policy documents, versioned prompt file, synthetic reference questions, bounded inline judge, trace export, and evaluation helpers. The completed GitHub Actions workflow stays in the instructor copy and is excluded from the student export.

## Classroom sequence

| Time | Work | Evidence |
|---|---|---|
| 0â€“35 minutes | Clone; configure the lab; run infrastructure and application bootstrap; configure Langfuse Cloud | Database, ingestion, frontend, authentication, and tracing readiness checks |
| 35â€“65 minutes | Inspect permissions and the inline judge; explain generation, bounded retry, fallback, and asynchronous monitoring | Authorized/denied requests; judge pass/retry/fallback examples |
| 65â€“105 minutes | Extracted prompt as code; package an immutable candidate; implement GitHub Actions local checks | Commit, prompt hash/version, dataset hash, artifact hash |
| 105â€“115 minutes | Break | |
| 115â€“160 minutes | Configure protected staging, AWS OIDC, secrets, candidate deployment, and real authenticated API evaluations | Running workflow and exact-release headers |
| 160â€“200 minutes | Compare reference assertions with judge results; repeated runs, uncertainty, human agreement | Candidate report; disagreements explained, not hidden |
| 200â€“225 minutes | Deliberately fail a quality gate, fix, rerun; inspect Langfuse experiment and report | Failed gate prevents promotion; successful rerun links to tested candidate |
| 225â€“240 minutes | Review OWASP evidence, drift demonstration, release ownership and rollback | Release recommendation, known gaps, recovery procedure |

The instructor demonstrates Promptfoo, DeepEval, Langfuse experiments and Evidently patterns. Tools may overlap deliberately. Prepared checkpoints are essential; installing and configuring every service from scratch would exceed four hours.

## Acceptance rules
Missing cases, API failures, wrong release identity, unauthorized data access, or incomplete evaluation block release. Domain-approved facts define expected answers. Judge scores do not enforce authorization and do not establish calibrated confidence. Synthetic classroom results are not a production error-rate guarantee.

## Before publishing this lab
Rehearse from a clean clone. Confirm ingestion completion and fresh synthetic-user authentication. Demonstrate real application traces, not just the connection smoke test. Finish the instructor workflow and its negative cases before claiming the release gate is complete.

See [the start-to-finish guide](HR-LAB-START-TO-FINISH.md) for detailed student actions.

Teaching constraint: minimal live coding. Students edit prompt text and connect short supplied workflow blocks. Python helpers run unchanged; use consoles, traces, reports and release evidence for the walkthrough.
