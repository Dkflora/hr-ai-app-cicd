# 06a2 Add the deployment jobs

**Goal:** add the `candidate` job to the workflow file. It deploys each merge to staging and evaluates it. Document 06a explains each of its steps.

Here you only change a file on your computer. You commit it in document 06b, after adding the GitHub settings the new jobs read. Without those settings, the first run would fail.

## Step 1: Append the candidate job

This command **adds** the `candidate` job to the end of the workflow file from document 04. The `>>` means "add to the end", so the lines already there stay as they are. Run it once only. Running it twice adds the jobs twice.

```bash
cd ~/hr-rag-lab
cat >> .github/workflows/hr-quality.yml <<'EOF'
  # Deploy the reviewed main commit, evaluate it, and approve only passing evidence.
  candidate:                                                            # job
    name: Deploy and evaluate staging                                   # job title
    # Secrets and AWS access are withheld from unreviewed pull-request code.
    if: >-                                                              # run condition
      always() && github.event_name != 'pull_request' && github.ref == 'refs/heads/main' &&
      needs.checks.result == 'success'
    needs: checks                                                       # depends on checks
    runs-on: ubuntu-24.04                                               # agent
    environment: hr-staging                                             # deploy environment
    timeout-minutes: 120                                                # time limit
    permissions:                                                        # token rights
      contents: read                                                    # read-only code
      id-token: write                                                   # AWS sign-in (OIDC)
      pull-requests: write                                              # PR comments
    env:                                                                # variables
      AWS_REGION: ${{ vars.AWS_REGION }}                                # setting
      HR_STAGING_FUNCTION: ${{ vars.HR_STAGING_FUNCTION }}
      HR_EVALUATION_FUNCTION: ${{ vars.HR_EVALUATION_FUNCTION }}
      HR_STAGING_ORIGIN: ${{ vars.HR_STAGING_ORIGIN }}
      HR_TEST_USERS_SECRET_ARN: ${{ vars.HR_TEST_USERS_SECRET_ARN }}
      HR_COGNITO_POOL_ID: ${{ vars.HR_COGNITO_POOL_ID }}
      HR_COGNITO_CLIENT_ID: ${{ vars.HR_COGNITO_CLIENT_ID }}
      LANGFUSE_PUBLIC_KEY: ${{ secrets.LANGFUSE_PUBLIC_KEY }}           # secret
      LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY }}
      LANGFUSE_BASE_URL: ${{ vars.LANGFUSE_BASE_URL }}
      HR_STAGING_FRONTEND_BUCKET: ${{ vars.HR_STAGING_FRONTEND_BUCKET }}
      HR_STAGING_DISTRIBUTION_ID: ${{ vars.HR_STAGING_DISTRIBUTION_ID }}
      VITE_AUTH_MODE: cognito                                           # build setting
      VITE_COGNITO_AUTHORITY: ${{ vars.VITE_COGNITO_AUTHORITY }}
      VITE_COGNITO_CLIENT_ID: ${{ vars.HR_COGNITO_CLIENT_ID }}
      VITE_COGNITO_DOMAIN: ${{ vars.VITE_COGNITO_DOMAIN }}
      EVAL_REPEATS: '2'                                                 # repeat each test
      EVAL_MAX_LATENCY_SECONDS: '20'                                    # slower answer fails
      EVAL_MIN_CONSISTENCY: '0.75'                                      # two answers must agree
      DO_NOT_TRACK: '1'                                                 # telemetry off
      DEEPEVAL_TELEMETRY_OPT_OUT: 'true'                                # telemetry off
    steps:                                                              # steps
      - uses: actions/checkout@v7                                       # get code
        with:                                                           # inputs
          persist-credentials: false                                    # drop Git token
      - uses: actions/setup-python@v7                                   # install Python
        with:
          python-version: '3.12'                                        # version
      - run: python -m pip install -r ci/requirements.txt               # install packages
      # Exchange GitHub identity for short-lived credentials in the scoped AWS role.
      - uses: aws-actions/configure-aws-credentials@v6                  # AWS sign-in
        with:
          role-to-assume: ${{ vars.AWS_STAGING_ROLE_ARN }}              # IAM role
          aws-region: ${{ vars.AWS_REGION }}                            # region
      - uses: actions/setup-node@v7                                     # install Node.js
        with:
          node-version: '22'
      # Build the UI from this commit and upload it to the staging frontend.
      - name: Build and deploy React to staging                         # step title
        run: |                                                          # script below
          npm --prefix frontend ci
          npm --prefix frontend run build
          python ci/deploy_frontend.py
      # Publish the prompt version and package it with the matching backend code.
      - name: Publish exact candidate prompt and package it
        run: python ci/release.py --publish                             # publish prompt, build zip
      - name: Deploy the new backend version to staging
        run: python ci/deploy_candidate.py                              # deploy Lambda version
      # Obtain fresh test-user tokens and run every reference case twice through the API.
      - name: Test the real authenticated application
        id: live                                                        # step ID
        run: python ci/evaluate_api.py                                  # API tests
      # Retrieval must return each case's expected policy, and the two answers must agree.
      - name: Check retrieval quality and answer consistency            # step title
        if: always() && steps.live.outcome != 'skipped'                 # run condition
        run: python ci/quality_checks.py                                # retrieval + consistency
      # Store captured answers and scores for version comparisons; no extra generation here.
      - name: Record the dataset experiment in Langfuse
        if: always() && steps.live.outcome != 'skipped'
        uses: langfuse/experiment-action@c7c4efe432e37d4e3693a018de469233c0018de4 # v1.0.12
        with:
          langfuse_public_key: ${{ secrets.LANGFUSE_PUBLIC_KEY }}
          langfuse_secret_key: ${{ secrets.LANGFUSE_SECRET_KEY }}
          langfuse_base_url: ${{ vars.LANGFUSE_BASE_URL }}
          experiment_path: ci/langfuse_experiment.py                    # script
          should_skip_sdk_installation: 'true'                          # skip install
          should_fail_on_regression: 'true'                             # fail on regression
          should_fail_on_script_error: 'true'                           # fail on error
          should_comment_on_pr: 'false'                                 # no PR comment
      - uses: actions/setup-node@v7                                     # install Node.js
        with:
          node-version: '22'
      - name: Independently assert captured API answers with Promptfoo
        if: always() && steps.live.outcome != 'skipped'
        run: python ci/prepare_promptfoo.py                             # build config
      # Assert expected facts, forbidden disclosures and sources in the captured answers.
      - name: Promptfoo evaluation action
        if: always() && steps.live.outcome != 'skipped'
        uses: promptfoo/promptfoo-action@04839e664f52212b877170219dab0d7ad2bf6440 # v1
        with:
          github-token: ${{ github.token }}                             # GitHub token
          config: ci/promptfoo.generated.json                           # config file
          promptfoo-version: '0.124.1'
          use-config-prompts: 'true'                                    # use config prompts
          force-run: 'true'                                             # always run
          fail-on-threshold: '100'                                      # 100% must pass
          no-share: 'true'                                              # no upload
          disable-comment: 'true'                                       # no PR comment
          no-cache: 'true'                                              # no cache
          no-table: 'true'                                              # short log
          no-progress-bar: 'true'                                       # short log
      # Model-graded checks on a sample: reference facts, faithfulness, relevancy, bias, toxicity.
      - name: Evaluate answer quality with DeepEval
        if: vars.ENABLE_DEEPEVAL == 'true'                              # optional
        run: |
          python -m pip install -r ci/requirements-demo.txt
          python ci/deepeval_check.py
      - name: Prepare Evidently numeric drift inputs
        if: always() && steps.live.outcome != 'skipped' && vars.ENABLE_EVIDENTLY == 'true'
        run: python ci/prepare_drift.py                                 # build CSV
      # Compare latency and answer-length distributions; drift is an investigation signal.
      - name: Evidently proxy drift report
        if: always() && steps.live.outcome != 'skipped' && vars.ENABLE_EVIDENTLY == 'true'
        uses: evidentlyai/evidently-report-action@7b255ad073b66f0a2f511393edf24d2907c15008 # v1
        with:
          config_path: ci/evidently_config.py:conf                      # checks
          input_path: build/drift-current.csv                           # this run
          reference_path: ci/data/drift-reference.csv                   # baseline
          output: build/evidently-report                                # output folder
          test_summary: 'false'                                         # no pass/fail
          save_dataset: 'false'                                         # skip data
          save_report: 'true'                                           # keep report
          upload_artifacts: 'true'                                      # attach report
          check-link: 'false'                                           # skip link check
      # Update the approved staging alias only after required preceding checks pass.
      - name: Approve the exact tested staging version
        if: success()                                                   # only if all passed
        run: python ci/promote_lab.py                                   # promote
      # Retain a sanitized report even when evaluation fails.
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
        uses: actions/github-script@v9                                  # GitHub API script
        with:
          script: |                                                     # JavaScript below
            const fs = require('fs');
            if (!fs.existsSync('build/report.md')) return;
            const pulls = await github.rest.repos.listPullRequestsAssociatedWithCommit({owner:context.repo.owner,repo:context.repo.repo,commit_sha:context.sha});
            const body = 'HR staging evaluation report (review all workflow jobs before release)\n\n' + fs.readFileSync('build/report.md','utf8');
            for (const pr of pulls.data) await github.rest.issues.createComment({owner:context.repo.owner,repo:context.repo.repo,issue_number:pr.number,body});
      - uses: actions/upload-artifact@v7                                # save artifacts
        if: always()                                                    # always save
        with:
          name: hr-candidate-evidence                                   # artifact name
          # Raw answers stay out. Score files quote parts of answers; a company keeps them in restricted storage.
          path: |                                                       # files below
            build/release.json
            build/report.md
            build/function.zip
            build/previous-approved.json
            build/deepeval.json
            build/quality.json
          retention-days: 3                                             # keep 3 days
EOF
grep -nE '^  (checks|candidate):' .github/workflows/hr-quality.yml
```

**Expected:** the last command prints two jobs: `checks` on line 15 and `candidate` on line 41.

## How to read the new job

The steps match the list in document 06a. A few parts of the YAML are new:

- `${{ vars.NAME }}` reads a GitHub **variable**, and `${{ secrets.NAME }}` reads a GitHub **secret**. You add both to the `hr-staging` environment in document 06b.
- `EVAL_REPEATS`, `EVAL_MAX_LATENCY_SECONDS` and `EVAL_MIN_CONSISTENCY` set how many times each question is asked, the time limit per answer, and the consistency pass mark. Change them here to change the gate.
- `id: live` names the API test step, so later steps can ask how it ended.
- `if: always() && steps.live.outcome != 'skipped'` means: run this step even if an earlier step failed, as long as the API test ran. Without `always()`, GitHub skips every step after a failure, and you would see no results.
- `if: success()` on the approval step means: run only if every earlier step passed.
- `if: vars.ENABLE_DEEPEVAL == 'true'` turns DeepEval on or off with a GitHub variable. Evidently has the same switch, `ENABLE_EVIDENTLY`.
- `actions/upload-artifact` keeps the listed files for 3 days, under **Artifacts** on the run page. The production and release jobs in document 06a3 read them from there.

If a job name appears twice, you ran the block twice. Create the file again with document 04, step 2, then run this block once.

**Next:** [06a3 Add the release jobs](06a3-add-release-jobs.md)
