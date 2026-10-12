# GitHub-to-AWS OIDC setup in the browser

Use this only if you do not already have a role for your own repository. Local AWS credentials are already configured. Students use the GitHub website and AWS console; no GitHub CLI is required.

## 1. Get your repository's exact subject prefix

Open your own repository's Settings and its Actions OIDC subject configuration. Copy the displayed subject prefix, including immutable owner/repository IDs if present. It must identify your own repository, not the instructor source. New repositories use a format such as `repo:USERNAME@OWNER-ID/hr-rag-lab@REPO-ID`.

If you cannot find that setting, the instructor can inspect the repository's OIDC configuration. Do not guess IDs or use wildcard repository trust. Custom OIDC subject templates need instructor review.

## 2. Generate the two policy files

After Terraform/app setup, run the inherited helper:

```bash
python scripts/prepare-oidc.py
```

It asks for your repository name (`username/hr-rag-lab`) and the exact subject prefix you copied. Region defaults to `us-east-1`. It reads local Terraform outputs and AWS account identity, then writes `build/github-oidc-trust.json` and `build/github-oidc-permissions.json`. It does not create AWS resources or require students to write Python.

Open both generated files in an editor. Trust is limited to your exact repository, `hr-lab-staging` environment and `sts.amazonaws.com` audience. Permissions target only your lab's Lambda/aliases, synthetic-user secret, Cognito pool, frontend bucket/distribution and Nova models.

## 3. Register the provider once per AWS account

In AWS console → IAM → Identity providers, find `token.actions.githubusercontent.com`. Reuse it if present and verify `sts.amazonaws.com` is an audience. If absent, choose Add provider → OpenID Connect, provider URL `https://token.actions.githubusercontent.com`, audience `sts.amazonaws.com`, and create it. Do not delete a shared provider or its other audiences.

## 4. Create the lab role in IAM

1. Open IAM → Roles → Create role → Custom trust policy.
2. Paste the JSON from `build/github-oidc-trust.json`.
3. Continue without attaching administrator policies. Choose a unique lab role name, such as `hr-ci-yourname-github-ci`, and create it.
4. Open the new role → Permissions → Add permissions → Create inline policy → JSON.
5. Paste `build/github-oidc-permissions.json`, review its scoped resources, and save it as `HRLabOnly`.
6. Copy the role ARN from the role summary.

If you lack permission to create IAM providers/roles/policies, the instructor or AWS account administrator performs these steps. If a role already exists, inspect it rather than overwriting unrelated trust or permissions.

## 5. Configure GitHub in the browser

Return to Section 5 of [the main lab guide](HR-LAB-START-TO-FINISH.md). Create `hr-lab-staging` and `hr-production-demo` in Settings → Environments. Add `AWS_STAGING_ROLE_ARN` as an environment variable using the copied role ARN, plus the other values listed in the guide. Add your Langfuse keys as environment secrets.

Restrict staging deployment to main and configure reviewer policy where available. Environment-scoped trust alone does not enforce a branch restriction; GitHub environment settings do. Use a public synthetic lab repository for GitHub Free environment support.

The supplied workflow already grants `id-token: write` and uses the official AWS credentials Action. It obtains temporary credentials; no AWS access-key secrets are needed.

## 6. Follow the pipeline

After reviewing and merging the workflow PR in the GitHub website, open Actions and select the new main run. Approve staging if required, then inspect the AWS sign-in step and the remaining jobs. A sign-in failure is usually a mismatch in subject prefix, environment, audience, provider account or branch rule. Do not fix it by broadening trust.

Sources: [GitHub OIDC in AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws), [subject formats](https://docs.github.com/en/actions/reference/security/oidc).
