# HR RAG: evaluation and CI/CD lab

This is a prepared application for the HR Week Six lab. Students already built the RAG workflow; this lab automates that setup and focuses on controlled changes, evaluations, release evidence, and recovery.

## Start the lab

First import this public repository into **your own GitHub account**. Use [GitHub Import](https://github.com/new/import), source `https://github.com/kserge2001/hr-rag-cicd-student-starter.git`, and choose yourself as the destination owner. Then clone your imported repository. The full guide includes a command-line import alternative. Cloning this source without creating your own repository is insufficient for configuring your pipeline.

Use Python 3.12, Node.js 22, Terraform, AWS CLI, and a Bash environment. Authenticate to your isolated AWS lab account. Copy `infra/terraform/terraform.tfvars.example` to `terraform.tfvars` in the same directory and choose unique lab names. Use one Aurora instance for the classroom rehearsal if appropriate. Store your Langfuse project keys in the ignored `.env.langfuse`, using `.env.langfuse.example` as the template. Confirm the project region endpoint.

Run `bash scripts/setup-lab.sh`. It creates a local Python environment, builds packages, runs Terraform, initializes the synthetic employee database, uploads policies, deploys React, initializes synthetic sign-in accounts, stores Langfuse keys securely, and checks ingestion plus an authenticated API request. Initial infrastructure creation can take several minutes. A failed readiness check is not a completed setup.

The API serves a `candidate` Lambda alias. The pipeline deploys a published numeric version and verifies release identity before grading answers. The separate `approved` alias is a classroom release pointer; this repository does not silently promote changes into an existing production application.

## Materials

- [Start-to-finish student guide](docs/HR-LAB-START-TO-FINISH.md)
- [Langfuse Cloud setup](docs/LANGFUSE-CLOUD-SETUP.md)
- [OWASP evidence review](docs/OWASP-EVIDENCE.md)
- [Original RAG implementation guide](docs/ORIGINAL-APPLICATION-GUIDE.md)

Students assemble the workflow from the blocks in the student guide. No active workflow is installed in the starter.

## What is automated and what is demonstrated

Terraform owns infrastructure; bootstrap code handles application setup. Python, prompt, React, and infrastructure files are reviewed together, with checks for their respective behavior. Prompts are validated structurally, published with an exact Langfuse version, and packaged with Python. Semantic correctness comes from running real application cases, not merely scanning prompt text.

Application spans go to CloudWatch and an outside-VPC exporter sends OTLP to Langfuse Cloud. No Langfuse credentials enter React or the private chat Lambda. Raw question/answer export is off by default and requires an explicit synthetic-staging switch. Post-run scoring is separate from the bounded inline judge, which can revise once and return a safe fallback.

GitHub Actions uses protected staging and AWS OIDC. Unreviewed PR code receives no cloud or model secrets. The instructor pipeline includes reference assertions, Promptfoo, Langfuse dataset experiments, optional DeepEval, reports, and a lab promotion pointer. Evidently needs its documented baseline. Tool installation alone does not establish security or answer quality.

## Working with the prepared application

Use the student guide to configure your own AWS deployment and GitHub pipeline. The setup script performs the application checks automatically. All evaluation helpers are supplied; students focus on the workflow, evidence and controlled changes.

Follow the class instructions for cleaning up your own AWS deployment when finished.
