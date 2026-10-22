# Reference: from this lab to production

This lab runs the whole life of an AI application, but at classroom size: one AWS account, one staging environment, and a release that becomes `approved` all at once. That keeps every run predictable, so the whole class sees the same thing.

A company running the HR assistant for real employees would add the practices below. For each one, this page says what the lab does, what production does, and how you could add it to this lab.

## 1. Separate environments and accounts

**In the lab:** one staging environment in your own AWS account. The production job is a dry run: it checks the tested version and prints what production would receive (document 16).

**In production:** staging and production live in **separate AWS accounts**. A mistake or a leaked permission in staging then cannot touch production data. The pipeline deploys to staging first. It promotes the same tested version to production only after the release gate passes and, often, after a person approves.

**How to add it here:** create a second account, and run the same Terraform there with production names. Then give the pipeline a second OIDC role that only the `hr-production-approval` environment may use. GitHub environments can require a named reviewer before a job runs, so the approval becomes a real person's click.

## 2. Infrastructure changes through the pipeline

**In the lab:** you run Terraform by hand from your computer, and its state file, the record of what Terraform created, stays in your folder.

**In production:** the state lives in shared storage, so the whole team works from the same record. Terraform's S3 backend keeps the state in an S3 bucket and uses a lock file, so two people cannot change the infrastructure at the same time. Every pull request shows `terraform plan`, the exact list of changes, for review. The merge applies it. Nobody changes production infrastructure from a laptop.

**How to add it here:** move the state to an S3 backend. Then add a pipeline job that runs `terraform plan` on pull requests and `terraform apply` after the merge. It signs in to AWS the same way as in document 06.

## 3. Releasing in steps: canary releases

**In the lab:** when a release passes, `approved` moves to it all at once.

**In production:** many teams send a new version to a small share of real traffic first. This is a **canary** release:

1. Send a small share of requests, such as 5 or 10%, to the new version. The rest stays on the approved version.
2. Watch the signals you already know: errors, answer time, and the 👎 rate.
3. If they stay healthy, raise the share step by step to 100%. If they get worse, send all traffic back to the approved version.

A canary catches what test cases miss, because real people ask questions nobody wrote down.

**How to add it here:** a Lambda alias can split traffic between two versions. This is called weighted routing. For example, this keeps the `approved` alias on version 21 and sends 10% of its requests to version 22:

```bash
aws lambda update-alias --function-name "$(terraform -chdir=infra/terraform output -raw candidate_function)" --name approved --function-version 21 --routing-config 'AdditionalVersionWeights={"22"=0.1}'
```

AWS CodeDeploy can run the steps for you, with modes such as "10% for 5 minutes, then everything". It also rolls back automatically when a CloudWatch alarm you name goes off, such as this lab's error or slow-answer alarms. In this lab, the staging app follows `candidate`, so a real canary would first need the app to follow `approved`.

## 4. A rollback strategy

**In the lab:** `ci/rollback_lab.py` moves `approved` back to the previous version (document 16).

**In production:** a team decides in advance **what** can be rolled back, **who** may do it, and **when**:

- **What:** the code version, the prompt, the model choice in the gateway's settings, and the policy index. Each needs its own way back. A rolled-back code version that expects a newer prompt or index can break.
- **Who:** anyone on call may roll back without asking. Rolling forward again goes through the normal pipeline.
- **When:** a written rule, such as "roll back if the 👎 rate doubles or errors pass 1% for 10 minutes after a release". Rolling back first and investigating after is usually faster than fixing in place.

## 5. Evaluation in production

**In the lab:** the release gate checks a fixed set of test questions before each release. People's 👍 and 👎 reach Langfuse, and a person reviews the 👎 answers (document 15).

**In production:** three more practices are common:

- **Grade live answers automatically.** Langfuse can run an AI judge on a sample of real traces, such as 5% of them. It saves its scores next to the votes. It finds bad answers even when nobody votes.
- **Check the AI judge against people.** The HR expert's grades in the review queue are the human answers. Comparing them with the judge's scores shows how far the judge can be trusted. This is called **calibrating** the judge. Until it is done, the judge's pass mark is a guess.
- **Grow the test cases from real failures.** Every confirmed mistake becomes a new test case, so the release gate learns from production.

**How to add it here:** create an evaluator in Langfuse for the `HR answer` traces with a low sampling rate. Then export the review queue's `failure_cause` scores and compare them with DeepEval's results on the same answers.

## 6. Monitoring with targets

**In the lab:** CloudWatch alarms for errors, server errors, slow answers and every single 👎, and the Langfuse dashboard **HR assistant health** (document 03).

**In production:** teams write down **service level objectives** (SLOs), targets that say how good is good enough. For example: "95% of answers in under 5 seconds", "fewer than 0.5% errors", "at least 85% thumbs up". Alarms then fire on the **rate** of problems against the target, not on single events. A single 👎 does not wake anyone up. A rising 👎 rate after a release does.

**How to add it here:** a CloudWatch alarm can compare two metrics, such as 👎 votes divided by all votes. The lab already counts the 👎 votes, so a second metric filter for all votes is enough to alert on a share.

## 7. On-call, runbooks and postmortems

**In the lab:** the [runbook](reference-runbook.md) lists what to do when the gate fails, an alarm fires, or the gateway is down.

**In production:**

- **On-call:** one named person per week receives the alarms, through a paging tool instead of a shared inbox.
- **Severity levels:** for example, "the assistant is down for everyone" is urgent at any hour, while "one wrong answer" waits for working hours.
- **Runbooks:** every alarm links to its runbook entry. Runbooks are kept current, like code.
- **Postmortems:** after an incident, the team writes what happened, how they found it, and what will prevent it next time. A postmortem never blames a person. Its actions often become new test cases or new alarms.

## 8. Security beyond the lab

**In the lab:** sign-in, row-level security, the guardrail, the private network, OIDC instead of keys, push protection, and code scans that report (documents 03, 05 and 06).

**In production:**

- Code scans **block** a merge on high findings, and a person reviews the rest.
- Keys and passwords are **rotated** on a schedule. The gateway master key and the test-account passwords in this lab never change.
- A **red team** tries new attacks on the assistant, beyond the fixed attack test cases. Successful attacks become new test cases.
- Logs and traces follow a written **retention** rule: how long they are kept, and who may read them.

## 9. Cost control

**In the lab:** every AI model call goes through the LiteLLM gateway. It caps spending at 5 US dollars a day for the app and 0.50 per person, and it limits each person's requests and tokens per minute. It records the cost of every call, by user and by purpose: `hr-chat` for answers, `inline-judge` for the live check, and `ci-judge` for the pipeline's judge. It also answers repeated questions from its cache. The Langfuse dashboard shows the model cost per day.

**This is the production pattern.** Companies control AI cost the same way. One gateway sits in front of every model, with budgets, rate limits and cost records per user, team or feature.

**What production adds:** two small things.

- **An alert when spending jumps,** before the budget stops people. For example, an alarm when today's cost is twice the usual day.
- **A budget alarm for the rest of the bill.** The gateway only sees model calls. The database, the gateway server and the private network connections cost money every hour too. AWS Budgets can email the team when the whole account's spending passes a set amount.
