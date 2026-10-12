# HR RAG lab: four hours from import to a passing pipeline

This lab inherits the AWS application and Python helpers. Students configure the lab, assemble three prepared workflow blocks, interpret evaluation results, deliberately break one setting, then fix and rerun. No application or evaluation script is written from scratch.

The instructor implementation passed 43/43 cases twice (86 authenticated API requests), with Promptfoo, Langfuse, DeepEval, Evidently and classroom promotion successful. [Baseline evidence](BASELINE-VERIFICATION.md) records the tested commit and run. A new student stack still needs its own readiness check and passing run.

## Schedule

| Minutes | Activity | Student work |
|---|---|---|
| 0–15 | Import, clone and orient | Create own repository, clone, create branch |
| 15–45 | Bootstrap | Local AWS/Langfuse configuration; one setup command |
| 45–65 | Inspect a request | Cognito login, user/session, tools, judge, prompt version |
| 65–105 | Build CI | Paste Block A; branch and PR checks |
| 105–115 | Break | |
| 115–155 | Wire staging | GitHub environment configuration; Blocks B/C; first passing release |
| 155–185 | Interpret tools | Assertions, experiment, semantic judge, drift report |
| 185–220 | Break, inspect, fix | One-number tool-budget failure and fixed rerun |
| 220–240 | Release and evidence | Promotion, production demonstration, recovery explanation |

The instructor chooses one live failure exercise. Other exercises are available in [FAILURE-EXERCISES.md](FAILURE-EXERCISES.md). Pipeline execution overlaps discussion. Initial AWS provisioning can exceed its slot; use the prepared deployment checkpoint if needed. Keep all infrastructure running.

## 1. Import, clone and orient (0–15)

Use Linux or WSL2 Bash for these commands, not PowerShell or Git Bash. Setup activates a Linux virtual environment. The workstation needs Git, GitHub CLI (`gh`), Python 3.12, Node.js 22/npm, Terraform 1.15.9, and AWS CLI. An instructor-hosted Linux workstation is another option. Missing tools use instructor setup support rather than consuming the evaluation segment.

The source repository is public. **Import it into your own GitHub account first**, then clone your imported repository. Cloning the instructor source alone does not give you ownership of its Actions settings or deployment environments.

1. Open [GitHub Import](https://github.com/new/import).
2. Enter `https://github.com/kserge2001/hr-rag-cicd-student-starter.git` as the source URL.
3. Choose **your own account** as owner and `hr-rag-lab` as the new repository name.
4. Choose **Public** for this synthetic classroom repository, then click **Begin import**. Private repositories require a GitHub plan that supports environment secrets; deployment-reviewer features also vary by plan. Wait for completion.
5. Open your new repository and confirm its address begins with your username. If GitHub Importer refuses a GitHub-hosted source, use the command-line import below; both create an independent student-owned repository.
6. Clone **your own repository** and create the classroom branch:

```bash
gh auth login
gh auth status
export GH_OWNER="$(gh api user --jq .login)"
export GH_REPO="$GH_OWNER/hr-rag-lab"
gh repo clone "$GH_REPO"
cd hr-rag-lab
git remote -v
git switch -c lab/classroom
```

The origin must point to your account, not `kserge2001`. You need repository administration access to configure Actions, secrets, environments and protections. If Actions is disabled, enable it in your repository Settings → Actions → General, using the class's policy for permitted actions.

### Command-line import alternative

Use this only if you have not already created `hr-rag-lab`. Do not initialize the destination with a README/license; import into an empty repository.

```bash
gh auth login
export GH_OWNER="$(gh api user --jq .login)"
export GH_REPO="$GH_OWNER/hr-rag-lab"
gh repo create "$GH_REPO" --public
git clone https://github.com/kserge2001/hr-rag-cicd-student-starter.git hr-rag-lab
cd hr-rag-lab
git remote rename origin source
git remote add origin "https://github.com/$GH_REPO.git"
git push -u origin main
git remote -v
git switch -c lab/classroom
```

This imports the starter's main-branch history into your own repository. No AWS roles, deployment environments, secrets or workflow runs are inherited from the source. Configure them later in this guide. The source's full workflow is in the guide as blocks; no active workflow runs just because you import.

Locate `frontend/`, `lambda/app/`, `lambda/app/prompts/hr_system.txt`, `infra/terraform/` and `ci/`. Explain login → authenticated API → authorized retrieval/tools → generation → inline judge → answer, with trace export to Langfuse.

## 2. Configure and bootstrap (15–45)

Authenticate to the isolated AWS lab account using the instructor-approved method. If using AWS IAM Identity Center:

```bash
aws configure sso --profile hr-lab
export AWS_PROFILE=hr-lab
export AWS_REGION=us-east-1
aws sso login --profile hr-lab
aws sts get-caller-identity --query Account --output text
python3 --version
node --version
terraform version
cp infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars
cp .env.langfuse.example .env.langfuse
```

Use a text editor to set these values in the ignored `terraform.tfvars`. Choose unique names; the placeholder below must be replaced by the student's own identifier.

```hcl
aws_region = "us-east-1"
project_name = "hr-ci-yourname"
cognito_domain_prefix = "northwind-hr-yourname"
domain_name = ""
aurora_instance_count = 1
langfuse_base_url = "https://us.cloud.langfuse.com"
inline_judge_enabled = true
trace_synthetic_content = true
```

The last flag exports approved synthetic classroom content for trace inspection. Do not enable it for unapproved real employee data.

Follow [LANGFUSE-CLOUD-SETUP.md](LANGFUSE-CLOUD-SETUP.md): sign up with GitHub or Google, create a project, select its region and create a key pair. Enter the keys into `.env.langfuse`; the public key starts `pk-lf-` and the secret starts `sk-lf-`. Use the project's matching endpoint. Quotes are optional. Save the file; do not paste secrets into chat, commits or React.

```bash
bash scripts/setup-lab.sh
source .venv/bin/activate
terraform -chdir=infra/terraform output -raw app_url
```

Bootstrap builds the Lambda layer, provisions infrastructure, initializes synthetic employees, uploads/ingests policies, deploys React, creates test sign-ins, stores Langfuse keys in Secrets Manager and verifies ingestion plus an authenticated API call. Do not redo the earlier manual chunking lesson. Terraform apply still requires plan review and confirmation.

Checkpoint: readiness succeeds, a real answer is returned, and model/tool observations reach Langfuse. A smoke trace alone is insufficient. Students using the prepared checkpoint must receive its local configuration/state through the instructor-approved arrangement; never run a new Terraform apply against someone else's stack accidentally.

## 3. Cognito and a real trace (45–65)

1. Inspect the existing Cognito pool, synthetic users and app client. The instructor supplies synthetic classroom sign-in credentials through an approved channel.
2. Sign into the chatbot. Explain the browser token → API Gateway → trusted claims → employee permissions flow. Do not display bearer tokens or passwords.
3. Ask "How many PTO days do employees receive each year?" and a follow-up. Find the session and opaque user identifier in Langfuse, then policy tool, model and inline judge spans. Inspect the numbered prompt version.
4. Explain `ci/auth.py` by its input and result: pipeline AWS permission allows admin authentication of synthetic users, credentials come from the lab secret, and fresh tokens remain in memory. It does not bypass API or data permissions.
5. Distinguish inline judging (before response, bounded revision/fallback) from Langfuse post-run scoring. Neither replaces access controls.

## 4. Build branch and PR checks (65–105)

Create `.github/workflows/hr-quality.yml` in the editor and paste **Block A** from the workflow section below. Keep its exact indentation. This block alone is a valid initial workflow.

```bash
mkdir -p .github/workflows
python -m unittest discover -s ci/tests -v
git add .github/workflows/hr-quality.yml
git commit -m "Add HR branch and pull-request checks"
git push -u origin lab/classroom
gh run list --branch lab/classroom --limit 3
gh pr create --base main --head lab/classroom --title "Add HR quality checks" --body "Run contract tests, package validation, Terraform validation and React build."
gh pr checks --watch
```

Inspect Actions and explain one actual test. Branch/PR code receives no AWS or Langfuse credentials. In repository Settings, configure main protection and required `checks` plus reviewer policy where available. The instructor reviews the PR. GitHub plan/organization features can restrict private-repository protections; state any unavailable control explicitly rather than claiming it exists.

## Break (105–115)

## 5. Wire protected staging (115–155)

If no role exists, follow [GITHUB-AWS-OIDC-SETUP.md](GITHUB-AWS-OIDC-SETUP.md) to generate reviewed policies and create a scoped role. Otherwise, the instructor supplies an AWS role ARN whose OIDC trust allows **this exact student repository** and `hr-lab-staging`, with audience `sts.amazonaws.com`. New repositories can use immutable owner/repository IDs in their OIDC subject; the instructor must inspect that configuration. Do not reuse the instructor rehearsal role or broaden trust to all repositories. Its scoped permissions cover only the student's lab Lambda/aliases, test-user secret, Cognito pool, frontend bucket/distribution and required model invocation. `lambda:GetFunction` is required by the update waiter.

Append **Block B** and **Block C** below to the same workflow file, keeping `candidate` and `production-demonstration` beneath `jobs`. Students do not write the Python helpers.

Configure GitHub from the local outputs using the inherited helper. Paste the role ARN supplied for this repository when prompted; it is an identifier, not an AWS secret.

```bash
read -r -p "Instructor-issued AWS role ARN for this repository: " AWS_STAGING_ROLE_ARN
python scripts/configure-github.py --repo "$GH_REPO" --role-arn "$AWS_STAGING_ROLE_ARN"
gh variable list --repo "$GH_REPO" --env hr-lab-staging
gh secret list --repo "$GH_REPO" --env hr-lab-staging
```

The helper creates `hr-lab-staging` and `hr-production-demo`, sets the following variables and stores Langfuse keys as encrypted environment secrets. It never prints secret values, creates AWS roles or configures reviewers.

| Variable | Source |
|---|---|
| AWS_REGION | Local AWS_REGION, us-east-1 for this class |
| AWS_STAGING_ROLE_ARN | Instructor-issued role for this repository |
| HR_STAGING_FUNCTION | candidate_function Terraform output |
| HR_STAGING_ORIGIN | app_url output |
| HR_TEST_USERS_SECRET_ARN | evaluation_users_secret_arn output |
| HR_COGNITO_POOL_ID / HR_COGNITO_CLIENT_ID | cognito_user_pool_id / cognito_client_id outputs |
| HR_STAGING_FRONTEND_BUCKET / HR_STAGING_DISTRIBUTION_ID | frontend_bucket / cloudfront_distribution_id outputs |
| VITE_COGNITO_AUTHORITY / VITE_COGNITO_DOMAIN | Generated frontend/.env.production |
| LANGFUSE_BASE_URL | Ignored .env.langfuse |
| ENABLE_DEEPEVAL / ENABLE_EVIDENTLY | true |

Secrets: LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY, read from the ignored local file. No long-lived AWS keys enter GitHub.

In Settings → Environments, restrict staging to main and configure a designated reviewer where available. Configure the production-demo reviewer too. A sole owner cannot approve their own protected deployment; arrange another reviewer or explicitly identify the classroom approval limitation.

```bash
git add .github/workflows/hr-quality.yml
git commit -m "Connect candidate deployment and AI evaluation gate"
git push
gh pr checks --watch
```

After instructor review, merge the open PR in GitHub. Merge to main triggers the protected deployment. Approve the environment when required, then:

```bash
gh run list --branch main --limit 3
# Paste the new main run ID from the list; do not watch an older passing run.
read -r -p "New main run ID: " RUN_ID
gh run watch "$RUN_ID" --exit-status
gh run view "$RUN_ID" --web
```

Inspect exact prompt publication, candidate deployment, 43 cases × two API requests, evaluation tools, report and approved pointer. All required results must pass. If readiness or deployment fails, inspect the actual failed step; do not skip jobs or weaken assertions.

## 6. Interpret the four tools (155–185)

- Promptfoo: deterministic required/prohibited facts and source assertions over captured real API answers.
- Langfuse: dataset experiment outputs and scores by numbered prompt/code release. The experiment replays captured outputs; it does not independently regenerate another sample.
- DeepEval: prepared reference-aware model grader. Examine one reason; a model grade can be wrong. The optional demonstration runs only when enabled and prior steps succeed.
- Evidently: numeric answer-length/latency comparison with a captured failing classroom reference. A distribution shift requests investigation, not automatic rejection of answer quality. Report generation must succeed when enabled.

Inspect results in Actions, Langfuse and the downloaded Evidently artifact. Compare cases and repeat counts before interpreting scores. Human agreement requires independent labels from a domain expert; classroom simulated labels are not real user-outcome validation. The illustrative uncertainty report does not establish a production mistake percentage.

## 7. Break, inspect, fix and rerun (185–220)

Use [FAILURE-EXERCISES.md](FAILURE-EXERCISES.md), Exercise 1. Start from the now-passing main branch:

```bash
git switch main
git pull --ff-only
git switch -c lab/tool-budget
```

In the editor, change only `MAX_TOOL_ROUNDS = 5` to `MAX_TOOL_ROUNDS = 1` in `lambda/app/assistant.py`.

```bash
git add lambda/app/assistant.py
git commit -m "Exercise: limit the agent to one tool round"
git push -u origin lab/tool-budget
gh pr create --base main --head lab/tool-budget --title "Exercise: demonstrate a blocked release" --body "Synthetic classroom failure; expect the live gate to fail and approved to remain unchanged."
gh pr checks --watch
```

Static checks can pass despite this behavior regression. After instructor review and merge, inspect the **new main run**, its failed live assertions and Langfuse trace. The tool lookup consumes the only round; the next answer-generation turn cannot occur. Confirm promotion/demo are skipped and approved remains the baseline. The classroom UI still uses candidate, so it can show the deliberately broken answer while release is blocked.

Fix with another short branch/PR:

```bash
git switch main
git pull --ff-only
git switch -c lab/restore-tool-budget
```

Restore `MAX_TOOL_ROUNDS = 5` in the editor.

```bash
git add lambda/app/assistant.py
git commit -m "Restore the working tool budget"
git push -u origin lab/restore-tool-budget
gh pr create --base main --head lab/restore-tool-budget --title "Restore the working tool budget" --body "Restore baseline behavior and rerun all reference cases."
gh pr checks --watch
```

After review and merge, use the run-list/watch commands above for the new main run. Keep the question/reference unchanged; compare failed/fixed traces, case results and exact release identity. All required evaluations must pass before promotion. If model variation causes an unrelated failure, investigate it.

## 8. Production demonstration, recovery and evidence (220–240)

The final job verifies the exact merged commit and passing report, then demonstrates a production handoff. It does not deploy a second stack or move production traffic. React, prompt and backend come from the same reviewed commit; initial Terraform changes require a separate reviewed apply.

Review the prepared `ci/rollback_lab.py` and prior approved-version evidence. Rehearse rollback only when the instructor confirms the previous version exists; do not roll back or destroy shared infrastructure automatically.

Submit branch/PR and bad/fixed run links, corresponding trace links, the passing report, tool-result explanations and release/recovery reasoning. Review [OWASP-EVIDENCE.md](OWASP-EVIDENCE.md); this lab does not certify complete security.

## Exact workflow blocks

Paste A first. Append B and C later in the same file. These blocks are the verified instructor workflow divided by job; no Python source needs copying. The starter deliberately has **no active workflow** until students assemble it.

### Block A — branch/PR checks

```yaml
# Students build this workflow using the completed version as a checkpoint.
name: HR application candidate and evaluation gate
on:
  pull_request:
  push:
    branches: [main, 'lab/**']
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
    environment: hr-lab-staging
    timeout-minutes: 120
    permissions:
      contents: read
      id-token: write
      pull-requests: write
    env:
      AWS_REGION: ${{ vars.AWS_REGION }}
      HR_STAGING_FUNCTION: ${{ vars.HR_STAGING_FUNCTION }}
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

### Block C — production handoff demonstration

```yaml
  production-demonstration:
    name: Demonstrate production release after merge
    if: github.event_name != 'pull_request' && github.ref == 'refs/heads/main'
    needs: candidate
    runs-on: ubuntu-latest
    environment: hr-production-demo
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
          print('No production resources or traffic are changed by this classroom job.')
          PY
```

## Command references

The GitHub CLI commands follow its official documentation: [GitHub Importer](https://docs.github.com/en/migrations/importing-source-code/using-github-importer/importing-a-repository-with-github-importer) and [create an empty destination repository](https://cli.github.com/manual/gh_repo_create), [set environment variables](https://cli.github.com/manual/gh_variable_set), and [set encrypted environment secrets](https://cli.github.com/manual/gh_secret_set). The prepared helper passes values through standard input.

GitHub documents these plan requirements in [Deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments).
