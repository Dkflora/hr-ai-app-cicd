# HR policy assistant: evaluation and delivery

An AI chatbot application deployed in AWS with React frontend, Python backend, authenticated policy retrieval, LiteLLM model routing, Langfuse tracing and automated release evaluations.

## Start here

Follow [the step-by-step guide](docs/guide/hr-rag-cicd.md) in order, from document 00 to 09. Each document ends with a link to the next.

Import this public repository into your own GitHub account before cloning. Your copy must own its Actions settings, environments and secrets. Document 01 gives the exact steps.

[The full reference](docs/HR-LAB-START-TO-FINISH.md) covers the same lab in one long page, with background on each service, the model gateway and the OWASP coverage. Where the two differ, follow the step-by-step guide.

## What the repository provides

- `frontend/`: the React application.
- `lambda/`: the Python backend, versioned prompt, synthetic employee/policy data and reference cases.
- `infra/terraform/`: infrastructure for initial setup, including the private model gateway.
- `scripts/`: automated application setup and configuration helpers.
- `ci/`: authenticated API tests, evaluation adapters, deployment and reporting helpers.
- `docs/guide/`: the step-by-step guide, documents 00 to 09 plus the test cases and troubleshooting.
- `docs/HR-LAB-START-TO-FINISH.md`: the full reference in one page.
- `OWNERS.md`: who owns each part of the repository, and what each owner checks in a review.

The starter contains no active GitHub Actions workflow. Create it using the code inside the guide. Model and tool permissions remain enforced by the backend; evaluation scores do not grant access.

## Delivery boundary

Reviewed changes deploy to one synthetic staging environment. Required evaluation failures block release approval. The production handoff is a dry run; it does not provision a separate production stack or move production traffic.
