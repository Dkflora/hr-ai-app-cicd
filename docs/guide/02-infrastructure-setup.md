# 02 Infrastructure setup

**Goal:** connect Langfuse, set your Terraform names, and deploy the whole application into your AWS account with one setup command.

The setup checks your machine first, then builds the backend and creates the infrastructure with Terraform. It then loads synthetic employees, indexes the policy documents, deploys the React site and creates the sign-in accounts. Finally it makes a real signed-in API call to prove it works.

## Step 1: Create a Langfuse project and keys

Langfuse records every request: the question, the tools called, the model calls and the judge result. Create the project first, because the next steps need its address and keys.

1. Open [Langfuse Cloud](https://cloud.langfuse.com) and sign in with GitHub or Google.
2. Create an organization, then a project named for the HR application.
3. Note your region's API address. For a US project it is `https://us.cloud.langfuse.com`.
4. Open project **Settings → API keys** and create a key pair. The public key starts `pk-lf-`, the secret key starts `sk-lf-`.

## Step 2: Create your two local settings files

Both files are git-ignored, so they never reach GitHub.

```bash
cd ~/hr-rag-lab
cp infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars
cp .env.langfuse.example .env.langfuse
```

## Step 3: Add your Langfuse keys to .env.langfuse

Fill in `.env.langfuse` with the key pair and address from step 1:

```ini
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com
```

Keep this key pair private. You will paste the same two keys into GitHub in document 06b.

## Step 4: Set your names in terraform.tfvars

Set these values in `infra/terraform/terraform.tfvars`, replacing `yourname` with something unique to you:

```hcl
aws_region = "us-east-1"
project_name = "hr-ci-yourname"
cognito_domain_prefix = "northwind-hr-yourname"
domain_name = ""
aurora_instance_count = 1
langfuse_base_url = "https://us.cloud.langfuse.com"
trace_synthetic_content = true
```

- `project_name`: Prefix for every AWS resource name. Two students with the same name collide.
- `cognito_domain_prefix`: Becomes part of the sign-in page address, which must be unique across all of AWS.
- `langfuse_base_url`: The same Langfuse address as in `.env.langfuse`. The setup stops if the two differ.
- `trace_synthetic_content`: `true` stores the synthetic questions and answers in traces so you can read them.

## What the setup builds

One command creates the whole application in your AWS account. The main parts:

- **Terraform:** the tool that creates the AWS resources from the files in `infra/terraform/`. It records what it created in a state file, so it can change or delete them later.
- **Cognito:** the sign-in service. It holds the demo employees and the pipeline's test accounts.
- **API Gateway and Lambda:** API Gateway receives each question and checks the sign-in token, then a Lambda function, the Python backend, answers it.
- **Aurora PostgreSQL:** the employee database, with row-level security so each person reads only what their role allows.
- **OpenSearch:** the search index of the policy documents. **Indexing** means splitting each document into passages and storing them so the app can search them.
- **Amazon Bedrock:** the AI models and the guardrail.
- **LiteLLM gateway:** a small server that every model call passes through.
- **S3 and CloudFront:** S3 stores the React web app, and CloudFront serves it over HTTPS.
- **Secrets Manager:** stores passwords and keys, so they never sit in code.

## Step 5: Start the setup

This creates billable AWS resources.

```bash
bash scripts/setup-lab.sh
```

First the script checks your tools, both settings files and your AWS account. If anything is missing, it lists every problem at once and stops before it installs or creates anything. Fix each item and run the same command again.

Each step then prints one line with a green check mark and how long it took, such as `✓ Python environment (.venv) (2s)`. The full output of every step goes to `build/setup.log`.

## Step 6: Review the plan and answer y

Before Terraform changes anything, the script prints the plan summary, such as `Plan: 129 to add, 0 to change, 0 to destroy.`, and asks `Apply these changes? [y/N]`. Your resource count may differ by a few. Before answering, check:

- On a first run, the summary says `0 to change, 0 to destroy`. Anything else means the wrong state or account.
- If the script lists resources under **These will be deleted or recreated**, read the list. On a first run it must be empty.
- The resource names in `build/setup.log` start with your own `project_name`.

If all three hold, type `y` and press Enter. Any other answer stops the script without changing anything.

## Step 7: Let the setup finish

Creating the infrastructure is the longest step. A timer shows how long it has been running. The script then continues on its own:

1. Creates the database tables, the demo employees and the pipeline's test accounts.
2. Starts the LiteLLM model gateway and waits until it is ready.
3. Uploads the policy documents; uploading `manifest.json` starts indexing.
4. Builds the React site and uploads it to S3 behind CloudFront.
5. Creates the sign-in accounts and stores their passwords in Secrets Manager.
6. Stores your Langfuse keys in Secrets Manager.
7. Checks that indexing finished and makes one signed-in API call as a test account.
8. Deletes the chat that check created, so the app starts with an empty history.

**Expected:** `Setup complete.`, followed by the app address, the demo employees and their password.

If a step fails, the script prints a red ✗, what to check, and the key error line. Fix the cause and run the same command again. The script is safe to rerun: steps whose inputs have not changed are skipped, and the others leave your deployment as it is.

## Step 8: Open the application

After `Setup complete.`, the script prints the app address, which starts with `https://`. It then lists the four demo employees you can sign in as, with their roles and the one password they share:

- `amara.diallo@northwind.example`: employee
- `liam.fischer@northwind.example`: manager
- `priya.raman@northwind.example`: hr
- `dana.whitfield@northwind.example`: exec

It also prints the sign-in for the LiteLLM gateway admin UI, which document 03 opens.

The same details are saved in `demo-sign-in.txt` in the project folder, so you can open them in your editor at any time. The file holds the gateway master key, so keep it on your computer. Run `python scripts/show-demo-users.py` to recreate it.

Setup also starts `build/github-settings.txt`, one file that collects every value GitHub will need in document 06b, each under the exact name GitHub expects. Document 05 adds the last value. Like everything in `build/`, it never reaches GitHub.

If you closed the terminal or lost the output, print the details again:

```bash
cd ~/hr-rag-lab
cat demo-sign-in.txt
```

Open the address in your browser. You should see the Northwind HR sign-in page.

Activate the virtual environment in every new terminal before running Python helpers:

```bash
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate
```

**Next:** [03 Sign in and read your first trace](03-sign-in-and-first-trace.md)
