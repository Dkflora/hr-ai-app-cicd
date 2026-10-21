# 05 GitHub-to-AWS access

**Goal:** let the pipeline deploy to AWS without storing any AWS keys in GitHub.

## What the pipeline does in AWS

In document 02, setup created every AWS resource, using your AWS sign-in. The pipeline creates nothing new. It uploads new code to those resources and tests it:

- **Lambda, chat function** (`deploy_candidate.py`, `promote_lab.py`): Uploads the new code, saves it as a new numbered version, and moves the `candidate` and `approved` labels. Document 06a explains these labels.
- **S3** (`deploy_frontend.py`): Uploads the built React website files.
- **CloudFront** (`deploy_frontend.py`): Clears its cache, so browsers load the new website.
- **Secrets Manager** (`evaluate_api.py`): Reads the password of the test accounts. It can read no other secret.
- **Cognito** (`evaluate_api.py`): Signs in as the `qa.*` test accounts.
- **Lambda, evaluation function** (`deepeval_check.py`): Runs the model that grades answers.

The live tests call the app the same way a browser does: through its public API, signed in with Cognito. Langfuse has its own keys, which you save in GitHub in document 06b.

## Why OIDC

The pipeline runs on a computer that GitHub provides. AWS needs proof of who is asking before it allows anything. One way is to store an AWS access key in GitHub. That key works until someone deletes it. Anyone who copies it from a log, or from a hacked action, could use it too.

GitHub Actions uses **OIDC** (OpenID Connect) instead. It works like this:

1. When a job starts, GitHub gives it a signed token. The token says which repository and which environment the job belongs to.
2. The job sends the token to AWS.
3. AWS checks GitHub's signature. Then it compares the token with the role's **trust policy**: the rules that say who may use the role. Here that is your repository, the `hr-staging` environment, and the audience `sts.amazonaws.com`.
4. If everything matches, AWS gives the job temporary credentials that expire within an hour.

No secret is stored anywhere, so there is nothing to leak or replace. A fork or another repository cannot use the role, because its token names a different repository. A job outside the `hr-staging` environment cannot use it either. In document 06b, you allow only `main` to use that environment. Azure DevOps calls the same idea workload identity federation.

## What the script does

One script, `scripts/prepare-oidc.py`, sets everything up in your AWS account. It does six things, in order:

1. Finds your GitHub repository from the folder's Git remote. This is the same address `git remote -v` shows.
2. Writes two policy files to `build/`. One says who may use the role. The other says what the role may do.
3. Checks both files. Only your repository's `hr-staging` environment may use the role. Every permission must name one of the project's resources in the AWS account you are signed in to. If anything is wrong, the script stops before it changes AWS.
4. Connects GitHub to AWS as an identity provider. If your account already has one, it reuses it.
5. Creates the deployment role, named after your project. If the role already exists, it updates it.
6. Prints the role's ARN, its full AWS name, and saves it in `build/github-oidc-role-arn.txt`.

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

The numbers after `@` are fixed IDs of your GitHub account and repository. GitHub adds them to the token for repositories created after 15 July 2026. So if someone later creates a repository with the same name, it cannot pass as yours.

You can run the script again safely. It updates the role and never deletes anything. To run only the checks, without changing AWS, add `--dry-run`.

To see each step the script takes, or to build the same role yourself in the AWS console, follow [Reference: OIDC by hand](reference-oidc-by-hand.md).

The script also writes the role ARN into `build/github-settings.txt`. In document 06b, you copy every GitHub value from that one file.

**Next:** [06a How the deployment jobs work](06a-how-the-deployment-jobs-work.md)
