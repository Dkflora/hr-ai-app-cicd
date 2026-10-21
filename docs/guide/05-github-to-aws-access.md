# 05 GitHub-to-AWS access

**Goal:** let the pipeline deploy to AWS without storing any AWS keys in GitHub.

## What the pipeline does in AWS

Setup in document 02 built every AWS resource with your own credentials. The pipeline creates nothing. It ships new code into those resources and tests it:

- **Lambda, chat function** (`deploy_candidate.py`, `promote_lab.py`): Uploads code, publishes a version, and moves the `candidate` and `approved` aliases.
- **S3** (`deploy_frontend.py`): Uploads the built React files.
- **CloudFront** (`deploy_frontend.py`): Clears the cache so browsers get the new UI.
- **Secrets Manager** (`evaluate_api.py`): Reads the test accounts' password, and only that secret.
- **Cognito** (`evaluate_api.py`): Signs in as the `qa.*` test accounts.
- **Lambda, evaluation function** (`deepeval_check.py`): Runs the model grader.

The live tests call the app's public API with a Cognito token, the way a browser does. Langfuse uses its own keys, stored in GitHub.

## Why OIDC

The pipeline runs on a GitHub machine, so it must prove to AWS who it is. A stored access key would work until someone deletes it, and anyone who copies it from a log or a compromised action could use it.

GitHub Actions uses **OIDC** (OpenID Connect) instead:

1. When a job starts, GitHub gives it a signed token that names the repository and the environment.
2. The job sends the token to AWS.
3. AWS checks the signature, then checks the token against your role's trust policy: your repository, the `hr-staging` environment, the `sts.amazonaws.com` audience.
4. If all match, AWS returns credentials that expire within an hour.

Nothing secret is stored, so nothing can leak or need rotating. A fork or another repository cannot use the role, because its token names a different repository. A job outside the `hr-staging` environment cannot either, and document 06b allows only `main` to use that environment. Azure DevOps calls the same idea workload identity federation.

## What the script does

One script, `scripts/prepare-oidc.py`, sets everything up in your AWS account:

1. Reads your repository from the folder's Git remote, the same address `git remote -v` shows.
2. Writes two policy files to `build/`: who may use the role, and what the role may do.
3. Checks both files. Only your repository's `hr-staging` environment may use the role, and every permission names one of your project's resources in your AWS account. Any problem stops the script before AWS changes.
4. Reuses the GitHub identity provider if your account has one, and creates it if not.
5. Creates the deployment role, named after your project, or updates it if it exists.
6. Prints the role ARN and saves it in `build/github-oidc-role-arn.txt`.

## Step 1: Run the script

```bash
cd ~/hr-rag-lab
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate
python scripts/prepare-oidc.py
```

**Expected**, with your own names and numbers:

- The `Repository` line names your repository, such as `kserge2001/hr-rag-lab-cicd`.
- The `Checked` line names your token subject, such as `repo:kserge2001@25421539/hr-rag-lab-cicd@1423681941`.
- It also says the 6 permissions are limited to your project's resources in your account.
- The last line is `Done.` and the role ARN, such as `arn:aws:iam::123456789012:role/hr-ci-ai-chatbot-github-ci`.

The numbers after `@` are your GitHub account's and repository's fixed IDs. GitHub puts them in the token for repositories created after 15 July 2026, so a repository later created with the same name cannot pass as yours.

Running the script again is safe: it updates the role and never deletes anything. Add `--dry-run` to run the checks without changing AWS.

To see each step the script takes, or to build the same role yourself in the AWS console, follow [Reference: OIDC by hand](reference-oidc-by-hand.md).

The script also adds the role ARN to `build/github-settings.txt`, the file document 06b copies every GitHub value from.

**Next:** [06a How the deployment jobs work](06a-how-the-deployment-jobs-work.md)
