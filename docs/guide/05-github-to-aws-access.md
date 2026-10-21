# 05 GitHub-to-AWS access

**Goal:** give the pipeline permission to change your AWS resources. You compare the two usual ways of doing that, then set up the safer one, OIDC.

## What the pipeline does in AWS

In document 02, setup created every AWS resource, using your AWS sign-in. The pipeline creates nothing new. It uploads new code to those resources and tests it:

- **Lambda, chat function** (`deploy_candidate.py`, `promote_lab.py`): Uploads the new code, saves it as a new numbered version, and moves the `candidate` and `approved` labels. Document 06a explains these labels.
- **S3** (`deploy_frontend.py`): Uploads the built React website files.
- **CloudFront** (`deploy_frontend.py`): Clears its cache, so browsers load the new website.
- **Secrets Manager** (`evaluate_api.py`): Reads the password of the test accounts. It can read no other secret.
- **Cognito** (`evaluate_api.py`): Signs in as the `qa.*` test accounts.
- **Lambda, evaluation function** (`deepeval_check.py`): Runs the model that grades answers.

The live tests call the app the same way a browser does: through its public API, signed in with Cognito. Lan## Two ways to give the pipeline AWS access

The pipeline runs on a computer that GitHub provides, not on yours. AWS needs proof of who is asking before it allows anything. There are two common ways to give that proof.

### Option 1: an access key stored in GitHub

You create an IAM user in AWS and give it an **access key**: a key ID and a secret, like a username and password for programs. You save both as secrets in GitHub. Each job reads them and signs in to AWS as that user.

This works, and many older pipelines still do it. It has these problems:

- **The key never expires.** It works until someone deletes it. If it leaks, it keeps working for whoever has it.
- **It can leak.** A job log, a compromised third-party action, or a debugging step that prints the environment can expose it.
- **Someone must rotate it.** Good practice is to replace the key regularly and update GitHub each time. This is manual work that teams often forget.
- **AWS sees only the IAM user.** CloudTrail, the AWS activity log, cannot tell which repository, branch or run used the key.

### Option 2: OIDC, with no stored key

**OIDC** (OpenID Connect) lets AWS trust GitHub directly. It works like this:

1. When a job starts, GitHub gives it a signed token. The token says which repository and which environment the job belongs to.
2. The job sends the token to AWS.
3. AWS checks GitHub's signature. Then it compares the token with the role's **trust policy**: the rules that say who may use the role. Here that is your repository, the `hr-staging` environment, and the audience `sts.amazonaws.com`.
4. If everything matches, AWS gives the job temporary credentials that expire within an hour.

This removes each problem above:

- **No secret is stored**, so there is nothing to leak, copy or rotate.
- **The credentials expire within an hour**, even if one leaks from a running job.
- **Only your repository's `hr-staging` environment can use the role.** A fork or another repository has a token that names a different repository. In document 06b, you allow only `main` to use that environment.
- **CloudTrail records who asked.** Each sign-in shows the repository and environment named in the token, not just a user name.

This lab uses OIDC. It is what AWS and GitHub recommend for pipelines. Azure DevOps calls the same idea workload identity federation.

t. Azure DevOps calls the same idea workload identity federation.

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

The numbers after `@` are fixed IDs of your GitHub account and repository. So if someone later creates a repository with the same name, it cannot pass as yours.

You can run the script again safely. It updates the role and never deletes anything. To run only the checks, without changing AWS, add `--dry-run`.

To see each step the script takes, or to build the same role yourself in the AWS console, follow [Reference: OIDC by hand](reference-oidc-by-hand.md).

The script also writes the role ARN into `build/github-settings.txt`. In document 06b, you copy every GitHub value from that one file.

**Next:** [06a How the deployment jobs work](06a-how-the-deployment-jobs-work.md)
