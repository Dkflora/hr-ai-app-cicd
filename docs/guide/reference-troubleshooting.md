# Reference: troubleshooting

Start with the failed step's log in GitHub Actions. The step name tells you which part to check.

## "Not authorized to perform sts:AssumeRoleWithWebIdentity"

AWS refused the workflow's identity. No HR test ran, so this is a sign-in problem, not an evaluation failure.

Check these four things match exactly:

1. `AWS_STAGING_ROLE_ARN` in the `hr-staging` environment is the role you created in document 05.
2. The `candidate` job has `id-token: write` and `environment: hr-staging`. The pasted workflow already has both.
3. The role's trust policy audience is `sts.amazonaws.com`.
4. The trust policy subject contains your exact repository identity and ends with `:environment:hr-staging`.

Check the subject format first. A name-only subject such as `repo:USERNAME/hr-rag-lab:environment:hr-staging` does not match a token that carries IDs, such as `repo:USERNAME@OWNER-ID/hr-rag-lab@REPO-ID:environment:hr-staging`.

To fix it, run the document 05 script again. It reads your repository's IDs from GitHub and updates the role's trust policy to match. If you switched an older repository to immutable subject claims yourself, add `--subject-prefix` with the ID form.

```bash
cd ~/hr-rag-lab
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate
python scripts/prepare-oidc.py
```

When it prints `Done.`, click **Re-run failed jobs** in GitHub.

Never copy another repository's IDs or use a wildcard to make it pass.

## The deployment jobs show as skipped

- **On a pull request**: Expected. Unreviewed code gets no AWS access, so `candidate` runs only after the merge to `main`.
- `production-handoff-dry-run` after a failed `candidate`: Expected. That is the release gate working.
- `candidate` on `main`: The `checks` job failed first. Fix that.

## The React build fails with a missing Cognito setting

The build stops when `VITE_COGNITO_AUTHORITY`, `VITE_COGNITO_CLIENT_ID` or `VITE_COGNITO_DOMAIN` is empty. The workflow fills `VITE_COGNITO_CLIENT_ID` from the `HR_COGNITO_CLIENT_ID` variable. Print the right values and add the missing variable to the `hr-staging` environment:

```bash
cd ~/hr-rag-lab
grep -E '^VITE_COGNITO_(AUTHORITY|DOMAIN)=' frontend/.env.production
terraform -chdir=infra/terraform output -raw cognito_client_id
```

## A job fails because a variable is empty

Variables must sit in the **hr-staging environment**, not under repository variables, and the names are case-sensitive. Compare your list with document 06b, step 3.

## The setup script stops

The script prints a red ✗ next to the step that failed, what to check, and the key error line. The full output is in `build/setup.log`. After fixing the cause, run the same command again; finished steps are skipped or repeated safely:

```bash
cd ~/hr-rag-lab
bash scripts/setup-lab.sh
```

If it stops at the first step, **Tools, configuration files and AWS account**, nothing has been created yet. The script lists every problem it found. The common ones:

- **Missing infra/terraform/terraform.tfvars** or **Missing .env.langfuse**: You skipped document 02, step 2.
- **Replace "yourname"**: You copied `terraform.tfvars` but did not set your own names.
- **Langfuse rejected the keys**: The keys in `.env.langfuse` are wrong, or `LANGFUSE_BASE_URL` is for another region.
- **AWS credentials do not work**: Run `aws configure` or `aws sso login`, then retry.
- **cognito_domain_prefix is already taken**: Someone else uses that prefix. Choose another in `terraform.tfvars`.
- **A stack named ... already exists**: That `project_name` is already deployed in this account, from another folder. Run setup from that folder, or choose another name.
- **Secret ... is still reserved**: A teardown with the same `project_name` left it. The message prints the command that releases it.

If the readiness check fails with the app deployed, wait a minute and run setup again. The first search after indexing can be slow.

## The app breaks right after you rerun setup

The UI and API call the chat function through the `candidate` alias, which points to one frozen version. A setup rerun can publish a new version, but only the pipeline moves `candidate`. The alias then keeps calling the older version, with the settings it froze. If one of those settings points at something setup replaced, every question fails, and so does the readiness check.

Compare the alias with the newest version:

```bash
cd ~/hr-rag-lab
FN="$(terraform -chdir=infra/terraform output -raw candidate_function)"
aws lambda get-alias --function-name "$FN" --name candidate --query FunctionVersion --output text
aws lambda list-versions-by-function --function-name "$FN" --query 'Versions[-1].Version' --output text
```

If the numbers differ, point `candidate` at the newest version, then run setup again so the readiness check passes:

```bash
aws lambda update-alias --function-name "$FN" --name candidate \
  --function-version "$(aws lambda list-versions-by-function --function-name "$FN" --query 'Versions[-1].Version' --output text)"
bash scripts/setup-lab.sh
```

After document 06b, your next merge to `main` also fixes it, because the pipeline publishes a version and moves `candidate`. Move it by hand only to repair setup. Never move `approved` by hand to make a release pass.

## A test case fails and you do not know why

1. Find the case number in the report, then look it up in [the test cases](reference-test-cases.md).
2. In Langfuse, find that question's trace from the run, using the time and test account.
3. Read the tool output: was the right policy passage retrieved?
4. Read the judge span: did it change or withhold the draft?

Investigate the answer, the retrieval or the grader. Never change the expected answer to make the case pass.
