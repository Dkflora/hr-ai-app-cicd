# Reference: runbook

A **runbook** is the page a person on call opens when something goes wrong. Each entry below says how you notice the problem, what to check first, and what to do. Every command runs in Git Bash, in your lab folder, with the virtual environment on:

```bash
cd ~/hr-rag-lab
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate
```

The alarm names start with your `project_name`, such as `hr-ci-yourname`. They are set in `infra/terraform/monitoring.tf`, and they email the addresses you subscribed in document 15.

## The release gate failed

**How you notice:** the run on `main` shows a red `candidate` job, and the report ends with `Release gate: FAIL.`

**Users are safe:** a failed release never moves `approved`. It still sits on the last passing version.

1. Open the run's **Summary** and read the report. If it says another step failed, open that step's log.
2. For a failing test case, open the **Promptfoo evaluation action** step's log. There, `case_id` counts from 0, so `case_id` 40 is case 41 in [the test cases](reference-test-cases.md).
3. Find that question's trace in Langfuse and read its steps: policy search, model calls, inline judge.
4. Fix it on a new branch, raise `VERSION`, and open a pull request, as in documents 12 to 14.

## A bad release is live

**How you notice:** people report wrong answers, the 👎 alarm fires again and again, or the share of thumbs up drops on the Langfuse dashboard **HR assistant health**.

Move `approved` back to the previous version:

```bash
python ci/rollback_lab.py
```

**Expected:** `approved now points to` the earlier release, and a `Rolled back` line. Document 16 explains what it changes. Then fix the cause through a normal pull request. The next passing run moves `approved` forward again.

## The thumbs-down alarm fired

**How you notice:** an email titled **ALARM:** with your `-thumbs-down` alarm name.

```bash
python scripts/review-thumbs-down.py
```

**Expected:** a line such as `Thumbs down in the last 7 days: 1. Newly queued: 1.` Then review each answer in the Langfuse queue **Thumbs-down review**, and pick its `failure_cause`, as in document 15. One vote is a signal, not an outage. Several in a short time after a release point to that release.

## Errors or server errors

**How you notice:** an email for the `-chat-errors` alarm (the chat function failed) or the `-api-5xx` alarm (people got server errors). People see `The assistant is unavailable right now. Try again in a moment.`

1. In the AWS console, open **CloudWatch → Log groups**, then your chat function's log group, `/aws/lambda/` followed by your `project_name` and `-chat`. Look for `assistant unavailable:` lines and the error after them.
2. If the error points to the model gateway, check it in the next entry.
3. If the errors started right after a release, roll back first and investigate after.

## The model gateway is down

**How you notice:** errors as above, and the gateway admin page from document 03 does not open.

Restart the gateway's container through Systems Manager, without signing in to the server:

```bash
aws ssm send-command --instance-ids "$(terraform -chdir=infra/terraform output -raw gateway_instance_id)" --document-name AWS-RunShellScript --parameters 'commands=["docker restart hr-litellm"]'
```

**Expected:** the command prints a JSON block with `"Status": "Pending"`. After about a minute, ask the app a question again. The gateway runs as the Docker container `hr-litellm`, next to its cache, `hr-redis`.

## Answers are slow

**How you notice:** an email for the `-chat-slow` alarm: the slowest 10% of answers took over 20 seconds, for 10 minutes.

1. On the Langfuse dashboard, check **Answer time p95 by release**. A jump after a release points to that release.
2. Open a slow trace and find the step that took the longest: policy search, model call or inline judge.
3. In the gateway admin page, under **Logs**, check whether model calls are slow or retried.

## People hit the usage limit

**How you notice:** people see `You've reached the assistant's usage limit. Wait a minute and try again.`

The gateway refused the call because a budget or rate limit was reached. The limits are 5 US dollars a day for the app, 0.50 per person, and per-minute request and token limits. They are set in `infra/terraform/gateway-bootstrap.sh.tftpl`. Check **AI model cost per day** on the Langfuse dashboard. A sudden rise can mean a loop or misuse, not real demand. Raise a limit only after you know why it was reached.
