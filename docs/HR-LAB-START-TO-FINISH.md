# HR policy assistant: controlled delivery and evaluation

This lab inherits the AWS application and Python helpers. We configure the deployment, assemble the workflow blocks, interpret evaluation results, reproduce a controlled failure, then fix and rerun. No application or evaluation script is written from scratch.

The application and evaluation helpers are supplied. Setup automatically checks the application; we then assemble and run our pipeline.

## How to use this guide

This is the single setup and delivery walkthrough. Follow the numbered sections in order. Open a linked reference only for the configuration or explanation you need at that step; do not combine manual deployment instructions with automated setup.

## Delivery model

This project follows this process: review the change → deploy the new version to staging → run evaluations → approve the release. Branch names describe the change, rather than the training session:

| Branch | Purpose |
|---|---|
| `feature/ci-quality-gate` | Add the delivery pipeline |
| `test/tool-budget-regression` | Reproduce a controlled failure in synthetic staging |
| `fix/restore-tool-budget` | Restore the tested behavior |
| `main` | Deploy the reviewed version to staging and run release checks |

Branch and PR checks run without deployment credentials. After review, main deploys a candidate to staging and evaluates the real authenticated API. Required checks block promotion when behavior is wrong or evidence is incomplete. The approved alias is a release pointer within this same staging stack; it does not isolate production traffic. The final production-handoff job is explicitly a dry run.

### From staging to production

The release path is: **merge to main → deploy to staging → pass evaluations → release approval → production deployment → smoke checks and monitoring**. A separate production branch is not required.

| Step | What this repository does | What a production service requires |
|---|---|---|
| Validate release | Deploy and evaluate the candidate in staging | The same checks against the intended release |
| Approve | Use the protected production-approval environment | An authorized release reviewer where required |
| Deploy production | Run a handoff demonstration without changing resources or traffic | Deploy the tested backend package and React build, with the exact prompt version, using a separately scoped production role and production configuration |
| Verify and recover | Retain staging results and the approved staging pointer | Check the authenticated production API and frontend, monitor errors and quality, and restore the last approved release if needed |

The production job supplied here stops at the handoff demonstration. To make it a real deployment, replace its dry-run step with production deployment and verification steps. Passing staging checks alone does not move production traffic, and the staging alias is not a production environment.

For a real production service, deploy the tested artifact and exact prompt version through a separately authorized production job, with production configuration, smoke checks, monitoring and rollback. This repository does not provision that production environment. A deliberately broken change is permitted here only as an authorized fault simulation in synthetic staging; do not treat it as normal practice for a live production branch.

Use each PR to describe the change, validation and release impact. Retain the failing and passing runs, traces and exact release versions as engineering evidence. Explain remaining limitations instead of equating a green workflow with guaranteed correctness or security.

## Engineering responsibilities and release rules

- The domain owner approves HR reference answers and escalation rules. Implementation changes must preserve authorization and approved policy evidence.
- The repository owner configures protected branches, deployment environments and repository-scoped AWS access. Require PR review and branch checks before merging where the GitHub plan supports them.
- The pipeline records the commit, prompt version, deployed Lambda version and evaluation results. A missing result or required failed check blocks release approval; changing expected answers to hide a regression is not a repair.
- The release owner reviews the passing evidence and authorizes the production handoff. Production deployment must use the tested artifact with production configuration, rather than rebuilding an untracked version.
- After a release, monitor application errors, latency, cost and answer quality. Assign an owner to investigate alerts and decide whether to roll back; a model score alone does not diagnose the incident.

**Environment boundary:** this repository implements one synthetic staging stack. Its UI follows the candidate alias, so a failing candidate can be visible there while the approved pointer stays unchanged. A production service must route users to its approved release and isolate candidate testing. The production-handoff job here is a dry run, not a production deployment.

Infrastructure changes require a reviewed Terraform plan and apply. The application pipeline does not automatically apply arbitrary infrastructure changes. The controlled failure exercises operate only in synthetic staging and must finish with restored behavior and a passing run.

## 1. Import, clone and orient

Use Linux or WSL2 Bash for these commands, not PowerShell or Git Bash. Setup activates a Linux virtual environment. The workstation needs Git, Python 3.12, Node.js 22/npm, Terraform 1.15.9, and AWS CLI. A managed Linux workstation is another option. Install the required tools before running setup.

The source repository is public. **Import it into your own GitHub account first**, then clone your imported repository. Cloning the source repository alone does not give you ownership of its Actions settings or deployment environments.

1. Open [GitHub Import](https://github.com/new/import).
2. Enter `https://github.com/kserge2001/hr-rag-cicd-student-starter.git` as the source URL.
3. Choose **your own account** as owner and `hr-rag-lab` as the new repository name.
4. Choose **Public** for this synthetic-data repository, then click **Begin import**. Private repositories require a GitHub plan that supports environment secrets; deployment-reviewer features also vary by plan. Wait for completion.
5. Open your new repository and confirm its address begins with your username. If GitHub Importer refuses a GitHub-hosted source, use the template option below; both create a repository owned by your account.
6. Clone **your own repository** and create the feature branch:

```bash
git clone https://github.com/YOUR-USERNAME/hr-rag-lab.git
cd hr-rag-lab
git remote -v
git switch -c feature/ci-quality-gate
```

Replace `YOUR-USERNAME` with your account name. The origin must point to your imported repository, not the source repository. Configure pull requests, Actions, secrets and environments in the GitHub website. No GitHub CLI installation or commands are used in this lab.

If the browser importer refuses this source, use **Use this template → Create a new repository** on the source page, select your own account, and name it `hr-rag-lab`. Then use the same `git clone` command above.

No AWS roles, environments, secrets or workflow runs are inherited from the source. Enable Actions in your own repository's Settings if necessary.

Locate `frontend/`, `lambda/app/`, `lambda/app/prompts/hr_system.txt`, `infra/terraform/` and `ci/`. Explain login → authenticated API → authorized retrieval/tools → generation → inline judge → answer, with trace export to Langfuse.

Costs are explained in [LAB-COSTS.md](LAB-COSTS.md); there is no verified fixed five-dollar daily total.

## 2. Configure and bootstrap

AWS credentials are already configured. Start directly with the Terraform and Langfuse configuration:

```bash
cp infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars
cp .env.langfuse.example .env.langfuse
```

Use a text editor to set these values in the ignored `terraform.tfvars`. Choose unique names; the placeholder below must be replaced by your own identifier.

```hcl
aws_region = "us-east-1"
project_name = "hr-ci-yourname"
cognito_domain_prefix = "northwind-hr-yourname"
domain_name = ""
aurora_instance_count = 1
langfuse_base_url = "https://us.cloud.langfuse.com"
trace_synthetic_content = true
```

The inline judge is already included and always runs in this prepared application. It checks the draft before display, allows one revision, and uses a safe fallback if validation still fails. It is part of the prepared application; no enable/disable choice is required. Langfuse post-run scoring is a separate evaluation pattern.

`langfuse_base_url` is the Langfuse Cloud endpoint for your project's region, not the HR app URL or the model endpoint. For a US Langfuse project, use `https://us.cloud.langfuse.com`.

`trace_synthetic_content = true` includes approved synthetic question/answer content in traces so we can inspect it.

Follow [LANGFUSE-CLOUD-SETUP.md](LANGFUSE-CLOUD-SETUP.md): sign up with GitHub or Google, create a project, select its region and create a key pair. Enter the keys into `.env.langfuse`; the public key starts `pk-lf-` and the secret starts `sk-lf-`. Use the project's matching endpoint. Quotes are optional. Save the file; do not paste secrets into chat, commits or React.

```bash
bash scripts/setup-lab.sh
source .venv/bin/activate
terraform -chdir=infra/terraform output -raw app_url
```

Bootstrap builds the Lambda layer, provisions infrastructure, initializes synthetic employees, uploads/ingests policies, deploys React, creates test sign-ins, stores Langfuse keys in Secrets Manager and verifies ingestion plus an authenticated API call. Ingestion is automated; no manual chunking steps are required. Terraform apply still requires plan review and confirmation.

Checkpoint: readiness succeeds, a real answer is returned, and model/tool observations reach Langfuse. A smoke trace alone is insufficient. Use only configuration and Terraform state for your own deployment; do not apply changes to someone else's stack.

## 3. Cognito and a real trace

1. Inspect the existing Cognito pool, synthetic users and app client. The project owner supplies synthetic test-account credentials through an approved channel.
2. Sign into the chatbot. Explain the browser token → API Gateway → trusted claims → employee permissions flow. Do not display bearer tokens or passwords.
3. Ask "How many PTO days do employees receive each year?" and a follow-up. Find the session and opaque user identifier in Langfuse, then policy tool, model and inline judge spans. Inspect the numbered prompt version.
4. Explain `ci/auth.py` by its input and result: pipeline AWS permission allows admin authentication of synthetic users, credentials come from the lab secret, and fresh tokens remain in memory. It does not bypass API or data permissions.
5. Distinguish inline judging (before response, bounded revision/fallback) from Langfuse post-run scoring. Neither replaces access controls.

## 4. Build branch and PR checks

Create `.github/workflows/hr-quality.yml` in the editor and paste **Block A** from the workflow section below. Keep its exact indentation. This block alone is a valid initial workflow.

```bash
mkdir -p .github/workflows
python -m unittest discover -s ci/tests -v
git add .github/workflows/hr-quality.yml
git commit -m "Add HR branch and pull-request checks"
git push -u origin feature/ci-quality-gate
```

In GitHub, click **Compare & pull request**, choose `main` as base and your feature branch as compare, then create the PR. Open its **Checks** tab and inspect Actions. Explain one actual test. Branch/PR code receives no AWS or Langfuse credentials. In repository Settings, configure main protection and required `checks` plus reviewer policy where available. A designated reviewer reviews the PR. GitHub plan/organization features can restrict private-repository protections; state any unavailable control explicitly rather than claiming it exists.

## Break

## 5. Wire protected staging

If no role exists, follow [GITHUB-AWS-OIDC-SETUP.md](GITHUB-AWS-OIDC-SETUP.md) to generate reviewed policies and create a scoped role. Otherwise, the project owner supplies an AWS role ARN whose OIDC trust allows **our exact repository** and `hr-staging`, with audience `sts.amazonaws.com`. New repositories can use immutable owner/repository IDs in their OIDC subject; the project owner must inspect that configuration. Do not reuse the another repository's role or broaden trust to all repositories. Its scoped permissions cover only our staging Lambda/aliases, test-user secret, Cognito pool, frontend bucket/distribution and required model invocation. `lambda:GetFunction` is required by the update waiter.

Append **Block B** and **Block C** below to the same workflow file, keeping `candidate` and `production-handoff-dry-run` beneath `jobs`. The Python helpers are supplied; we configure the workflow blocks.

In the GitHub website, open **your repository → Settings → Environments → New environment**. Create `hr-staging` and `hr-production-approval`.

Open `hr-staging`. Under **Environment variables**, click **Add environment variable** for each name in the table below. Read the values from Terraform outputs and the generated frontend file:

```bash
terraform -chdir=infra/terraform output
```

For one exact value, use `terraform -chdir=infra/terraform output -raw OUTPUT_NAME`, replacing `OUTPUT_NAME` with the table's output name. Get the AWS role ARN from the OIDC console walkthrough or your AWS account administrator. Use `us-east-1` for this deployment.

Under **Environment secrets**, click **Add environment secret** for `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY`, using your saved local key pair. Keys remain outside source code and React. 

| Variable | Source |
|---|---|
| AWS_REGION | us-east-1 |
| AWS_STAGING_ROLE_ARN | Repository-scoped role created through the OIDC walkthrough |
| HR_STAGING_FUNCTION | candidate_function Terraform output |
| HR_EVALUATION_FUNCTION | evaluation_function Terraform output |
| HR_STAGING_ORIGIN | app_url output |
| HR_TEST_USERS_SECRET_ARN | evaluation_users_secret_arn output |
| HR_COGNITO_POOL_ID / HR_COGNITO_CLIENT_ID | cognito_user_pool_id / cognito_client_id outputs |
| HR_STAGING_FRONTEND_BUCKET / HR_STAGING_DISTRIBUTION_ID | frontend_bucket / cloudfront_distribution_id outputs |
| VITE_COGNITO_AUTHORITY / VITE_COGNITO_DOMAIN | Generated frontend/.env.production |
| LANGFUSE_BASE_URL | Ignored .env.langfuse |
| ENABLE_DEEPEVAL / ENABLE_EVIDENTLY | true |

Secrets: LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY, read from the ignored local file. No long-lived AWS keys enter GitHub.

In Settings → Environments, restrict staging to main and configure a designated reviewer where available. Configure the production-approval reviewer too. If self-review prevention is enabled, the person initiating a deployment cannot approve it; assign another reviewer. Document any approval features unavailable on your GitHub plan.

```bash
git add .github/workflows/hr-quality.yml
git commit -m "Connect candidate deployment and AI evaluation gate"
git push
```

Open the existing PR in GitHub, confirm its Checks tab passes, and obtain reviewer approval. Then merge the PR in the browser. Merge to main triggers the protected deployment. Approve the environment when required, then:

Open your repository's **Actions** tab, select the newest main-branch run for this merge, and follow the jobs. Approve the staging deployment when required. Read the job summary and logs in the browser; do not select an older passing run.

Inspect exact prompt publication, candidate deployment, 43 cases × two API requests, evaluation tools, report and approved pointer. All required results must pass. If readiness or deployment fails, inspect the actual failed step; do not skip jobs or weaken assertions.

## 6. Interpret the four tools

- Promptfoo: deterministic required/prohibited facts and source assertions over captured real API answers.
- Langfuse: dataset experiment outputs and scores by numbered prompt/code release. The experiment replays captured outputs; it does not independently regenerate another sample.
- DeepEval: prepared reference-aware model grader. Examine one reason; a model grade can be wrong. The optional demonstration runs only when enabled and prior steps succeed.
- Evidently: numeric answer-length/latency comparison with a captured failing nonproduction reference. A distribution shift requests investigation, not automatic rejection of answer quality. Report generation must succeed when enabled.

Inspect results in Actions, Langfuse and the downloaded Evidently artifact. Compare cases and repeat counts before interpreting scores. Human agreement requires independent labels from a domain expert; simulated labels are not real user-outcome validation. The illustrative uncertainty report does not establish a production mistake percentage.

## 7. Break, inspect, fix and rerun

Use [FAILURE-EXERCISES.md](FAILURE-EXERCISES.md), Exercise 1. Start from the now-passing main branch:

```bash
git switch main
git pull --ff-only
git switch -c test/tool-budget-regression
```

In the editor, change only `MAX_TOOL_ROUNDS = 5` to `MAX_TOOL_ROUNDS = 1` in `lambda/app/assistant.py`.

```bash
git add lambda/app/assistant.py
git commit -m "Exercise: limit the agent to one tool round"
git push -u origin test/tool-budget-regression
```

In the GitHub website, open a PR from `test/tool-budget-regression` into `main` and inspect its Checks tab. Static checks can pass despite this behavior regression. After reviewer approval and merge, inspect the **new main run**, its failed live assertions and Langfuse trace. The tool lookup consumes the only round; the next answer-generation turn cannot occur. Confirm promotion/demo are skipped and approved remains the baseline. The staging UI still uses candidate, so it can show the deliberately broken answer while release is blocked.

Fix with another short branch/PR:

```bash
git switch main
git pull --ff-only
git switch -c fix/restore-tool-budget
```

Restore `MAX_TOOL_ROUNDS = 5` in the editor.

```bash
git add lambda/app/assistant.py
git commit -m "Restore the working tool budget"
git push -u origin fix/restore-tool-budget
```

In GitHub, open a PR from `fix/restore-tool-budget` into `main`, inspect checks and obtain review. After merge, select the newest main run in the Actions tab. Keep the question/reference unchanged; compare failed/fixed traces, case results and exact release identity. All required evaluations must pass before promotion. If model variation causes an unrelated failure, investigate it.

## 8. Production handoff, recovery and evidence

The final job verifies the exact merged commit and passing report, then demonstrates a production handoff. It does not deploy a second stack or move production traffic. React, prompt and backend come from the same reviewed commit; initial Terraform changes require a separate reviewed apply.

Review the prepared `ci/rollback_lab.py` and prior approved-version evidence. Run rollback only after confirming the previous approved version exists; do not roll back or destroy shared infrastructure automatically.

Retain branch/PR and failing/fixed run links, corresponding trace links, the passing report, tool-result explanations and release/recovery reasoning. Review [OWASP-EVIDENCE.md](OWASP-EVIDENCE.md); this lab does not certify complete security.

## Understand the supplied automation

Read [the CI helper map](../ci/README.md) for every script, its purpose, and why it is needed. It distinguishes official tool Actions, application-specific adapters, deployment helpers and additional analysis. The helpers are supplied; configure and connect their workflow steps rather than copy Python source.

## Exact workflow blocks

Paste A first. Append B and C later in the same file. These blocks define the delivery workflow by job; no Python source needs copying. The starter deliberately has **no active workflow** until we assemble it.

### Block A — branch/PR checks

```yaml
# Reviewed changes, staging evaluation and release approval.
name: HR application candidate and evaluation gate
on:
  pull_request:
  push:
    branches: [main, 'feature/**', 'fix/**', 'test/**']
  workflow_dispatch:
permissions:
  contents: read
concurrency:
  group: hr-staging
  cancel-in-progress: false
jobs:
  checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install delivery helper dependencies
        run: python -m pip install -r ci/requirements.txt
      - name: Prompt structure and release contract tests
        run: python -m unittest discover -s ci/tests -v
      - name: Build Lambda artifacts required by Terraform validation
        run: |
          python ci/release.py
          bash scripts/build-layer.sh
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_wrapper: false
          terraform_version: '1.15.9'
      - name: Terraform formatting and static validation
        run: |
          terraform -chdir=infra/terraform fmt -check
          terraform -chdir=infra/terraform init -backend=false
          terraform -chdir=infra/terraform validate
      - name: Build backend candidate with release identity
        run: python ci/release.py
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: npm --prefix frontend ci
      - run: npm --prefix frontend run build
```

### Block B — protected candidate and evaluation gate

```yaml
  candidate:
    # Secrets and AWS access are withheld from unreviewed pull-request code.
    if: >-
      always() && github.event_name != 'pull_request' && github.ref == 'refs/heads/main' &&
      needs.checks.result == 'success'
    needs: checks
    runs-on: ubuntu-latest
    environment: hr-staging
    timeout-minutes: 120
    permissions:
      contents: read
      id-token: write
      pull-requests: write
    env:
      AWS_REGION: ${{ vars.AWS_REGION }}
      HR_STAGING_FUNCTION: ${{ vars.HR_STAGING_FUNCTION }}
      HR_EVALUATION_FUNCTION: ${{ vars.HR_EVALUATION_FUNCTION }}
      HR_STAGING_ORIGIN: ${{ vars.HR_STAGING_ORIGIN }}
      HR_TEST_USERS_SECRET_ARN: ${{ vars.HR_TEST_USERS_SECRET_ARN }}
      HR_COGNITO_POOL_ID: ${{ vars.HR_COGNITO_POOL_ID }}
      HR_COGNITO_CLIENT_ID: ${{ vars.HR_COGNITO_CLIENT_ID }}
      LANGFUSE_PUBLIC_KEY: ${{ secrets.LANGFUSE_PUBLIC_KEY }}
      LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY }}
      LANGFUSE_BASE_URL: ${{ vars.LANGFUSE_BASE_URL }}
      HR_STAGING_FRONTEND_BUCKET: ${{ vars.HR_STAGING_FRONTEND_BUCKET }}
      HR_STAGING_DISTRIBUTION_ID: ${{ vars.HR_STAGING_DISTRIBUTION_ID }}
      VITE_AUTH_MODE: cognito
      VITE_COGNITO_AUTHORITY: ${{ vars.VITE_COGNITO_AUTHORITY }}
      VITE_COGNITO_CLIENT_ID: ${{ vars.HR_COGNITO_CLIENT_ID }}
      VITE_COGNITO_DOMAIN: ${{ vars.VITE_COGNITO_DOMAIN }}
      EVAL_REPEATS: '2'
      DO_NOT_TRACK: '1'
      DEEPEVAL_TELEMETRY_OPT_OUT: 'true'
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: python -m pip install -r ci/requirements.txt
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.AWS_STAGING_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
      - name: Build and deploy React to isolated staging
        run: |
          npm --prefix frontend ci
          npm --prefix frontend run build
          python ci/deploy_frontend.py
      - name: Publish exact candidate prompt and package it
        run: python ci/release.py --publish
      - name: Deploy to isolated staging and wait
        run: python ci/deploy_candidate.py
      - name: Test the real authenticated application
        id: live
        run: python ci/evaluate_api.py
      - name: Record the dataset experiment in Langfuse
        if: always() && steps.live.outcome != 'skipped'
        uses: langfuse/experiment-action@76731c8b04fc7f962af689207690d414a0ee4de7 # v1.0.11
        with:
          langfuse_public_key: ${{ secrets.LANGFUSE_PUBLIC_KEY }}
          langfuse_secret_key: ${{ secrets.LANGFUSE_SECRET_KEY }}
          langfuse_base_url: ${{ vars.LANGFUSE_BASE_URL }}
          experiment_path: ci/langfuse_experiment.py
          should_skip_sdk_installation: 'true'
          should_fail_on_regression: 'true'
          should_fail_on_script_error: 'true'
          should_comment_on_pr: 'false' 
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
      - name: Independently assert captured API answers with Promptfoo
        if: always() && steps.live.outcome != 'skipped'
        run: python ci/prepare_promptfoo.py
      - name: Promptfoo evaluation action
        if: always() && steps.live.outcome != 'skipped'
        uses: promptfoo/promptfoo-action@04839e664f52212b877170219dab0d7ad2bf6440 # v1
        with:
          github-token: ${{ github.token }}
          config: ci/promptfoo.generated.json
          promptfoo-version: '0.124.1'
          use-config-prompts: 'true'
          force-run: 'true'
          fail-on-threshold: '100'
          no-share: 'true'
          disable-comment: 'true'
          no-cache: 'true'
          no-table: 'true'
          no-progress-bar: 'true' 
      - name: Additional DeepEval judge demonstration
        if: vars.ENABLE_DEEPEVAL == 'true'
        run: |
          python -m pip install -r ci/requirements-demo.txt
          python ci/deepeval_check.py
      - name: Prepare Evidently numeric drift inputs
        if: always() && steps.live.outcome != 'skipped' && vars.ENABLE_EVIDENTLY == 'true'
        run: python ci/prepare_drift.py
      - name: Evidently proxy drift report
        if: always() && steps.live.outcome != 'skipped' && vars.ENABLE_EVIDENTLY == 'true'
        uses: evidentlyai/evidently-report-action@7b255ad073b66f0a2f511393edf24d2907c15008 # v1
        with:
          config_path: ci/evidently_config.py:conf
          input_path: build/drift-current.csv
          reference_path: ci/data/drift-reference.csv
          output: build/evidently-report
          test_summary: 'false'
          save_dataset: 'false'
          save_report: 'true'
          upload_artifacts: 'true'
          check-link: 'false'
      - name: Promote the exact tested version to the lab release pointer
        if: success()
        run: python ci/promote_lab.py
      - name: Publish public-safe report
        if: always()
        run: |
          if test -f build/evaluation.json; then
            python ci/report.py
            cat build/report.md >> "$GITHUB_STEP_SUMMARY"
          else
            echo 'Evaluation did not complete; release is blocked.' >> "$GITHUB_STEP_SUMMARY"
          fi
      - name: Report on associated pull requests
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            if (!fs.existsSync('build/report.md')) return;
            const pulls = await github.rest.repos.listPullRequestsAssociatedWithCommit({owner:context.repo.owner,repo:context.repo.repo,commit_sha:context.sha});
            const body = 'HR staging evaluation report (review all workflow jobs before release)\n\n' + fs.readFileSync('build/report.md','utf8');
            for (const pr of pulls.data) await github.rest.issues.createComment({owner:context.repo.owner,repo:context.repo.repo,issue_number:pr.number,body});
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: hr-candidate-evidence
          # Raw answers are intentionally excluded; inspect them only in approved restricted storage.
          path: |
            build/release.json
            build/report.md
            build/function.zip
            build/previous-approved.json
          retention-days: 3
```

### Block C — production handoff (dry run)

```yaml
  production-handoff-dry-run:
    name: Production handoff (dry run)
    if: github.event_name != 'pull_request' && github.ref == 'refs/heads/main'
    needs: candidate
    runs-on: ubuntu-latest
    environment: hr-production-approval
    permissions:
      contents: read
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: hr-candidate-evidence
          path: evidence
      - name: Verify exact tested release and show production handoff
        env:
          EXPECTED_COMMIT: ${{ github.sha }}
        run: |
          python - <<'PY'
          import json, os
          from pathlib import Path
          release=json.loads(Path('evidence/release.json').read_text())
          report=Path('evidence/report.md').read_text()
          if release['commit'] != os.environ['EXPECTED_COMMIT']:
              raise SystemExit('Release does not match the merged commit')
          if 'Release gate: PASS.' not in report:
              raise SystemExit('A passing evaluation report is required')
          print('DEMONSTRATION ONLY: production would receive the tested backend artifact and exact prompt version.')
          print('React would be built from this same commit with production configuration.')
          print('No production resources or traffic are changed by this dry-run job.')
          PY
```

## Command references

See [GitHub Importer](https://docs.github.com/en/migrations/importing-source-code/using-github-importer/importing-a-repository-with-github-importer). Configure variables and secrets through the environment settings in your repository.

GitHub documents these plan requirements in [Deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments).

See [the change, test and evidence map](CHANGE-TEST-EVIDENCE-MAP.md) for what we edit, all 43 application cases, the executing helper or Action, and generated outputs.

Read [the LLM gateway guide](LLM-GATEWAY.md) for routing, Aurora separation, configured allowances, tests and remaining production requirements. Gateway setup runs inside the provided bootstrap command.
