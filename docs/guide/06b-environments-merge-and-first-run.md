# 06b Environments, merge and first run

**Goal:** give the deployment jobs their settings, merge the pull request, and watch the first full release run.

After this document, every merge to `main` deploys to staging, tests the real signed-in API, and approves the version only if every required check passes.

## What a GitHub environment is

A GitHub **environment** is a named place a job deploys to, with its own settings and rules:

- **Variables:** plain settings, such as the function name or the AWS region. Anyone with access to the repository can read them.
- **Secrets:** encrypted values, such as API keys. GitHub hides them in logs, and nobody can read them back after saving.
- **Deployment rules:** which branches may deploy there, and whether a person must approve each deployment first.

A job uses an environment with `environment:` in the workflow. The `candidate` job uses `hr-staging`, and AWS trusts only jobs in that environment. The production job uses `hr-production-approval`, where an approval rule can make a person sign off first.

## Step 1: Create the two GitHub environments

In your repository: **Settings → Environments → New environment**. Create:

- `hr-staging`
- `hr-production-approval`

## Step 2: Open the settings file

Every value for this document is in one file, written by setup in document 02 and completed by document 05. Refresh it, then open it in your editor:

```bash
cd ~/hr-rag-lab
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate
python scripts/github-settings.py
```

**Expected:** `GitHub settings: wrote build/github-settings.txt (15 variables, 2 secrets).` If it lists anything as `still missing`, the line names the document that creates it.

Open `build/github-settings.txt`. Each name is on one line, with its value on the next, in the same order as steps 3 and 4. Copy each name and value from there, exactly as shown.

## Step 3: Add the staging variables

Open **Settings → Environments → hr-staging**. Under **Environment variables**, click **Add environment variable** once for each name under `ENVIRONMENT VARIABLES` in the file:

- `AWS_REGION`, `AWS_STAGING_ROLE_ARN`
- `HR_STAGING_FUNCTION`, `HR_EVALUATION_FUNCTION`, `HR_STAGING_ORIGIN`
- `HR_TEST_USERS_SECRET_ARN`, `HR_COGNITO_POOL_ID`, `HR_COGNITO_CLIENT_ID`
- `HR_STAGING_FRONTEND_BUCKET`, `HR_STAGING_DISTRIBUTION_ID`
- `VITE_COGNITO_AUTHORITY`, `VITE_COGNITO_DOMAIN`, `LANGFUSE_BASE_URL`
- `ENABLE_DEEPEVAL`, `ENABLE_EVIDENTLY`

The `VITE_COGNITO` values are public settings. The React build bakes them into the JavaScript, and the build stops if one is missing.

## Step 4: Add the two secrets

On the same `hr-staging` page, under **Environment secrets**, click **Add environment secret** for each name under `ENVIRONMENT SECRETS` in the file: `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY`.

These are the only secrets in GitHub. AWS access comes from the OIDC role.

## Step 5: Protect the environments

- `hr-staging`: under **Deployment branches**, allow only `main`. Add a required reviewer if your plan offers it.
- `hr-production-approval`: add a required reviewer if your plan offers it.

If self-review prevention is on, the person who started a run cannot approve it, so pick another reviewer. Write down any feature your plan does not offer.

## Step 6: Push and merge

```bash
git add .github/workflows/hr-quality.yml
git commit -m "Connect staging deployment and AI evaluation gate"
git push
```

1. Open your existing pull request. Its `checks` job runs again and must pass.
2. The deployment jobs show as **skipped** on the pull request. That is the security rule working: unreviewed code gets no AWS access.
3. If someone reviews your work, ask them to approve. Otherwise review the changes yourself, then click **Merge pull request**.

## Step 7: Watch the first release run

1. Open the **Actions** tab and select the **newest** run on `main`, the one your merge started.
2. Approve the `hr-staging` deployment if it asks for approval.
3. Follow the `candidate` job: prompt publication, deployment, 104 API answers, the retrieval and consistency check, the evaluation tools, approval and report.
4. Open the run **Summary** to read the report.
5. Approve `hr-production-approval` if asked, and read the dry-run output.

**Expected:** every job green, and the report says `Release gate: PASS.`

After it passes, open the application, click **Sign in**, and confirm the Cognito sign-in page loads. The API tests do not cover the browser sign-in.

Confirm that both pointers moved to the version this run published. In the AWS console:

1. Check that the region at the top right is **N. Virginia (us-east-1)**.
2. Open **Lambda → Functions**, then your chat function: your `project_name` followed by `-chat`.
3. Open the **Aliases** tab.

**Expected:** two rows, `candidate` and `approved`, with the same version number. Click `approved` to see its description, which records the version it replaced. The **Versions** tab lists every version the pipeline has published.

The same check from the terminal:

```bash
FN="$(terraform -chdir=infra/terraform output -raw candidate_function)"
aws lambda list-aliases --function-name "$FN" --query 'Aliases[].[Name,FunctionVersion]' --output table
```

To see the run's model calls, open the gateway admin UI as in document 03, step 5, and go to **Logs**. The evaluation calls come from the test accounts.

If a step fails, open that step's log and fix the cause. Never skip a job or weaken a test to get green. AWS sign-in errors are covered in [Troubleshooting](reference-troubleshooting.md).

## Step 8: Update your local main and mark the baseline

Bring your local `main` up to date, then tag it `baseline`. The use cases restore files from this tag.

```bash
git switch main
git pull --ff-only
git tag baseline
git log --oneline -3
git rev-parse baseline
```

**Save for later:** the link to this passing run, the commit printed by the last command, and the prompt version shown in Langfuse. Every use case compares against this baseline.

**Next:** [07 Read the evaluation results](07-read-the-evaluation-results.md)
