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

## Step 2: Print the values for the staging variables

This prints every value you need, already labelled with its GitHub variable name:

```bash
cd ~/hr-rag-lab
while read -r variable output; do
  printf '%-28s %s\n' "$variable" "$(terraform -chdir=infra/terraform output -raw "$output")"
done <<'EOF'
HR_STAGING_FUNCTION candidate_function
HR_EVALUATION_FUNCTION evaluation_function
HR_STAGING_ORIGIN app_url
HR_TEST_USERS_SECRET_ARN evaluation_users_secret_arn
HR_COGNITO_POOL_ID cognito_user_pool_id
HR_COGNITO_CLIENT_ID cognito_client_id
HR_STAGING_FRONTEND_BUCKET frontend_bucket
HR_STAGING_DISTRIBUTION_ID cloudfront_distribution_id
EOF
grep -E '^VITE_COGNITO_(AUTHORITY|DOMAIN)=' frontend/.env.production
grep '^LANGFUSE_BASE_URL=' .env.langfuse
```

## Step 3: Add the staging variables

Open **Settings → Environments → hr-staging**. Under **Environment variables**, click **Add environment variable** once for each row:

- `AWS_REGION`: `us-east-1`.
- `AWS_STAGING_ROLE_ARN`: The role ARN from document 05.
- `HR_STAGING_FUNCTION`: From step 2.
- `HR_EVALUATION_FUNCTION`: From step 2.
- `HR_STAGING_ORIGIN`: From step 2.
- `HR_TEST_USERS_SECRET_ARN`: From step 2.
- `HR_COGNITO_POOL_ID`: From step 2.
- `HR_COGNITO_CLIENT_ID`: From step 2.
- `HR_STAGING_FRONTEND_BUCKET`: From step 2.
- `HR_STAGING_DISTRIBUTION_ID`: From step 2.
- `VITE_COGNITO_AUTHORITY`: From step 2, the text after `=`.
- `VITE_COGNITO_DOMAIN`: From step 2, the text after `=`.
- `LANGFUSE_BASE_URL`: From step 2, the text after `=`.
- `ENABLE_DEEPEVAL`: `true`.
- `ENABLE_EVIDENTLY`: `true`.

The `VITE_COGNITO` values are public settings. The React build bakes them into the JavaScript, and the build stops if one is missing.

## Step 4: Add the two secrets

On the same `hr-staging` page, under **Environment secrets**, click **Add environment secret** twice:

- `LANGFUSE_PUBLIC_KEY`: The `pk-lf-` key from your `.env.langfuse`.
- `LANGFUSE_SECRET_KEY`: The `sk-lf-` key from your `.env.langfuse`.

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
3. Follow the `candidate` job: prompt publication, deployment, 90 API answers, the four evaluation tools, approval and report.
4. Open the run **Summary** to read the report.
5. Approve `hr-production-approval` if asked, and read the dry-run output.

**Expected:** every job green, and the report says `Release gate: PASS.`

After it passes, open the application, click **Sign in**, and confirm the Cognito sign-in page loads. The API tests do not cover the browser sign-in.

Confirm that both pointers moved to the version this run published:

```bash
FN="$(terraform -chdir=infra/terraform output -raw candidate_function)"
aws lambda list-aliases --function-name "$FN" --query 'Aliases[].[Name,FunctionVersion]' --output table
```

**Expected:** `candidate` and `approved` show the same version number.

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
