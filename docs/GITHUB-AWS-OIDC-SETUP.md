# Connect GitHub Actions to AWS with OIDC

Run this after application bootstrap and before Section 5 of the classroom guide if no instructor-provided role exists. No Python code is written in class. The inherited helper generates policies; the student/instructor reviews them and creates a dedicated role.

## Permissions and identity

Sign into GitHub CLI and the isolated lab AWS account. Creating an IAM provider/role/policy requires account permission; if the student lacks it, the instructor or account administrator performs these steps. Do not substitute administrator credentials in GitHub.

```bash
gh auth status
aws sts get-caller-identity --query Account --output text
export GH_REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
export AWS_REGION=us-east-1
python scripts/prepare-oidc.py --repo "$GH_REPO" --region "$AWS_REGION"
```

Review `build/github-oidc-trust.json` and `build/github-oidc-permissions.json` in an editor. Trust must name exactly this repository's verified subject prefix, the `hr-lab-staging` environment and `sts.amazonaws.com` audience. New repositories can include immutable owner/repository IDs; the helper reads the actual prefix from GitHub, rather than guessing. Custom subject templates require instructor review.

Permissions must target only this lab's Lambda/aliases, synthetic-user secret, Cognito pool, frontend bucket/distribution and Nova models. The role does not apply Terraform or access arbitrary employee data. Lambda's waiter needs `lambda:GetFunction` as well as `GetFunctionConfiguration`.

## Register the provider once per AWS account

In AWS IAM → Identity providers, look for `token.actions.githubusercontent.com`. Reuse it if present; verify its audience list includes `sts.amazonaws.com` without deleting existing audiences. If absent, choose Add provider → OpenID Connect, provider URL `https://token.actions.githubusercontent.com`, audience `sts.amazonaws.com`, and complete creation. This shared account provider is not created once per student repository.

## Create the dedicated role

Use a unique role name derived from the lab function. Review the generated trust and permission files before these AWS mutations.

```bash
export ROLE_NAME="$(terraform -chdir=infra/terraform output -raw candidate_function)-github-ci"
aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document file://build/github-oidc-trust.json
aws iam put-role-policy --role-name "$ROLE_NAME" --policy-name HRLabOnly --policy-document file://build/github-oidc-permissions.json
export AWS_STAGING_ROLE_ARN="$(aws iam get-role --role-name "$ROLE_NAME" --query Role.Arn --output text)"
python scripts/configure-github.py --repo "$GH_REPO" --role-arn "$AWS_STAGING_ROLE_ARN"
```

If the role name already exists, inspect it with the instructor. Do not overwrite an unrelated role or broaden its trust. If the secret uses a customer-managed KMS key, the administrator must separately evaluate scoped decrypt permission; the rehearsed lab uses the default Secrets Manager encryption.

## Finish GitHub setup and prove it works

The helper creates the staging/demo environments and fills variables/secrets. In repository Settings → Environments, restrict staging deployment to main and set reviewer policy where available. The environment-scoped subject alone does not restrict branches: GitHub environment protection must enforce the allowed branch. A sole author cannot self-approve a protected deployment; arrange a reviewer or identify the classroom limitation.

The supplied candidate block already grants `id-token: write` and uses the official AWS credentials action with the configured role ARN and region. No AWS access-key secrets are needed.

Merge the reviewed workflow PR. Open the new main run, approve staging if required, and confirm the AWS sign-in step succeeds before candidate deployment. A role can take a short time to propagate; retry after checking the configuration.

If sign-in fails, compare repository subject prefix, environment name, audience, provider account and deployment branch rule. Do not resolve a mismatch with wildcard repository trust. Continue with the main guide's live application evaluations; successful AWS sign-in alone is not a passing lab.

Sources: [GitHub OIDC in AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws), [GitHub subject formats](https://docs.github.com/en/actions/reference/security/oidc).
