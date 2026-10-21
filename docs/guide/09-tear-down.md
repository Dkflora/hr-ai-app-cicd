# 09 Tear down

**Goal:** delete everything the lab created, so billing stops.

The private network endpoints, the gateway instance and the WAF keep billing every hour until they are deleted. Asking no more questions does not stop them.

Tear down after your last use case and after saving your evidence links. Run it on the machine that ran the setup: Terraform deletes only what its local state file records. Workflow runs, Langfuse traces and pull-request history stay available afterwards. The AWS stack and its `approved` alias do not.

## Step 1: Stop new deployments

In GitHub, open **Actions → HR application delivery and evaluation → ⋯ → Disable workflow**.

Otherwise a merge to `main` after teardown would try to deploy into deleted resources.

## Step 2: Run the teardown script

```bash
cd ~/hr-rag-lab
python scripts/tear-down.py
```

The script does the rest in order:

1. Reads your project's names from Terraform.
2. Runs `terraform destroy`, which lists everything it will delete and asks for `yes`. Check that every name carries your own `project_name`, then type `yes`.
3. Deletes the pipeline's role from document 05. Terraform did not create it.
4. Deletes `demo-sign-in.txt`, `.env.langfuse` and `build/github-settings.txt` from your folder.
5. Lists anything in AWS still tagged with your project.

Add `--release-names` if you will set up the lab again with the same `project_name`. AWS otherwise keeps two secret names reserved for 30 days. Add `--dry-run` to see what it would delete without deleting anything.

**Expected:** `Deleted the role`, then `Nothing tagged Project=` followed by your project name and `is left in AWS.`

If `terraform destroy` stops on a dependency error, run the script again. It continues from what is left. The tag index can lag behind deletes, so if the script lists something, open it in the AWS console to check whether it still exists.

The GitHub identity provider stays, because other projects in your account may use it.

## Step 3: Revoke the Langfuse keys

1. In Langfuse, open project **Settings → API keys** and revoke the key pair used in this lab.
2. In GitHub, open **Settings → Environments → hr-staging** and delete the `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` secrets.

Check **AWS Billing** the next day to confirm the charges have stopped.
