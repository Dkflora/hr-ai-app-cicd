# Reference: OIDC by hand

`scripts/prepare-oidc.py` in document 05 does everything on this page in one command. Follow this page instead if you want to see each step, or to build the same setup yourself in the AWS console. The result is the same role, with the same name, so documents 06b and 09 work either way.

## Step 1: Write the two policy files

The script's dry run writes both files and checks them, without changing anything in AWS:

```bash
cd ~/hr-rag-lab
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate
python scripts/prepare-oidc.py --dry-run
```

It prints the role name it would create, such as `hr-ci-ai-chatbot-github-ci`: your `project_name` followed by `-github-ci`. Note it for step 3.

The two files are in `build/`:

- `github-oidc-trust.json`: who may use the role. Only your repository's `hr-staging` environment, with the audience `sts.amazonaws.com`.
- `github-oidc-permissions.json`: what the role may do. Six permissions, one per service listed at the top of document 05.

## Step 2: Register GitHub as an identity provider

AWS checks GitHub's tokens only once it knows GitHub as an identity provider. You do this once per AWS account.

1. In the AWS console, open **IAM → Identity providers**.
2. If `token.actions.githubusercontent.com` is already listed, open it and check that `sts.amazonaws.com` is one of its audiences. Then go to step 3.
3. Otherwise, click **Add provider** and fill in:
   - Provider type: **OpenID Connect**
   - Provider URL: `https://token.actions.githubusercontent.com`
   - Audience: `sts.amazonaws.com`
4. Click **Add provider**.

Other projects in your account may use the same provider. Never delete it or remove its other audiences.

## Step 3: Create the role with the trust policy

1. Open **IAM → Roles** and click **Create role**.
2. Under **Trusted entity type**, choose **Custom trust policy**.
3. Delete the example policy in the editor, paste the whole contents of `build/github-oidc-trust.json`, and click **Next**.
4. On **Add permissions**, select nothing and click **Next**. The permissions come from the second file in step 4.
5. Name the role exactly as the dry run printed, such as `hr-ci-ai-chatbot-github-ci`, and click **Create role**.

## Step 4: Add the permissions as an inline policy

1. Open the new role. On its **Permissions** tab, click **Add permissions → Create inline policy**.
2. Switch the editor to **JSON**, delete the example, paste the whole contents of `build/github-oidc-permissions.json`, and click **Next**.
3. Name the policy `HRLabOnly` and click **Create policy**.

## Step 5: Save the role ARN

On the role's summary page, copy the **ARN**. Save it where the script would, then refresh the settings file for document 06b:

```bash
cd ~/hr-rag-lab
echo "PASTE-THE-ROLE-ARN-HERE" > build/github-oidc-role-arn.txt
python scripts/github-settings.py
```

Replace `PASTE-THE-ROLE-ARN-HERE` with the ARN before you run it.

**Expected:** `GitHub settings: wrote build/github-settings.txt`, with no `still missing` line.

## Check your work

Run the script's dry run again. It finds your role by name, so it plans no new one:

```bash
python scripts/prepare-oidc.py --dry-run
```

**Expected:** the plan says `Role` followed by your role name and `already exists`.
