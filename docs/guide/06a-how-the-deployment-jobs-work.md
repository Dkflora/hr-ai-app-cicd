# 06a How the deployment jobs work

**Goal:** understand what the deployment jobs do, before you add them to your workflow in document 06a2.

There is nothing to run in this document.

## The big picture

Every merge to `main` starts the same chain of jobs. In plain words:

1. **Check** the code: tests and a build. This is the `checks` job from document 04.
2. **Deploy** the new version to **staging**: the company's pre-production copy of the app. The engineers, the HR domain expert who reviews the answers, and the pipeline all use it before a version is approved.
3. **Test** the deployed app by asking it real questions, the way an employee would.
4. **Decide:** if every test passed, mark this version as **approved**. If any test failed, stop. The failing version is never approved.
5. **Report** what happened, pass or fail.
6. **Hand off** to production. In this lab that last job only prints what production would receive.

Step 4 is the **release gate**: the point where a failed test blocks the release. Jobs 2 to 5 are the `candidate` job. Job 6 is `production-handoff-dry-run`.

## How a version is deployed: Lambda versions and aliases

The app's backend runs on AWS Lambda. Lambda keeps every release as a separate, numbered copy:

- **Version:** a numbered copy of the code and its settings, such as version 7 or 8. Once created, a version never changes.
- **Alias:** a name that points to one version, and can be moved to another. The app is called through the alias name, so moving the alias switches every caller to the new version at once.

If you know Git: versions are like commits, and aliases are like branches.

The chat function has two aliases:

- **`candidate`** points to the newest version, the one being tested. The pipeline moves it on every merge. The staging app you sign in to uses it.
- **`approved`** points to the last version that passed every test. The pipeline moves it only when the release gate passes.

So when a merge breaks something, `candidate` points to the broken version and `approved` still points to the last good one. The staging app shows the broken answers, because it follows `candidate`. Documents 07a to 07c use this to show a failure safely.

Right now the chat function has only `candidate`. The first passing run in document 06b creates `approved`.

## What the candidate job does, in order

Each item is one step in the workflow file, with the script or action it runs.

**Before it starts**
- **Runs only on `main`, and only after `checks` passed.** A pull request never gets AWS access or secrets, so unreviewed code cannot touch AWS.

**Sign in and deploy**
- **Sign in to AWS** (`configure-aws-credentials`): uses the role from document 05. AWS gives the job credentials that expire within the hour.
- **Deploy the web app** (`ci/deploy_frontend.py`): builds the React UI from this commit and uploads it.
- **Publish the prompt** (`ci/release.py --publish`): saves the system prompt in Langfuse as a numbered version, linked to this commit.
- **Deploy the backend** (`ci/deploy_candidate.py`): uploads the code as a new Lambda version and moves `candidate` to it.

**Test**
- **Ask the real app** (`ci/evaluate_api.py`): signs in as the test accounts and asks every question in [the test cases](reference-test-cases.md), twice each. One wrong answer fails the step.

**Evaluate the answers**
- **Langfuse, Promptfoo, DeepEval and Evidently** each score the captured answers in their own way. The next section explains each one.

**Decide and report**
- **Approve** (`ci/promote_lab.py`): moves `approved` to this version, only if every step above passed.
- **Report** (`ci/report.py`): writes a summary on the run page and on the pull request. It never includes employees' answers.

When the API test fails, Langfuse, Promptfoo, Evidently and the report still run, so you can see what broke. **Approve** is skipped, and so is DeepEval.

## The four evaluation tools

All four read the same captured answers, so they add no model calls to the app. Each one tests something different.

### Promptfoo: the fact checks

**What it is:** an open-source tool for testing LLM output against written rules, often run in CI.

**What it tests here:** every answer, from both runs of every case, against that case's rules in [the test cases](reference-test-cases.md):

- It contains every **required fact**, such as `5` for the carry-over question.
- It contains none of the **forbidden facts**, such as another employee's salary.
- It cites the expected policy as a **source**.

Upper and lower case do not matter, and neither do commas, `$` or `*`. The threshold is 100%: one broken rule fails the step. It repeats the live API test's checks independently, with a standard tool whose results anyone can read.

**Where the result appears:** the **Promptfoo evaluation action** step log in the run.

### DeepEval: a model grades the answer

**What it is:** an open-source framework for **LLM-as-a-judge**: a second model scores an answer against a written rubric.

**What it tests here:** the first 3 cases. The judge model gets the question, the answer and the case's required and forbidden facts. Its rubric, named `HR reference outcome`, says:

- Penalize a missing required fact or a disclosed forbidden fact.
- Accept a refusal when the case requires one.
- Do not penalize an answer that corrects a false claim in the question.

Each score runs from 0 to 1, and the pass mark is 0.7.

A judge can be wrong, so DeepEval adds a second opinion. It never replaces the fact checks.

**Where the result appears:** the **Evaluate answer quality with DeepEval** step log.

### Evidently: drift

**What it is:** an open-source tool that compares new data with reference data and reports what shifted. A shift is called **drift**.

**What it tests here:** two numbers per answer, its length and its response time, compared with a stored reference run. It reports, but it never fails the run. A shift is a reason to look at the answers, not proof that one is wrong.

**Where the result appears:** the run's **Artifacts**, as an HTML report.

### Langfuse: traces, prompts and experiments

You met Langfuse traces in document 03. The pipeline uses three more of its features:

- **Prompts:** each run publishes the system prompt as a new numbered version of `hr-policy-system`, labelled `candidate` and tagged with the commit. Every trace links to the version that produced it.
- **Datasets:** the test cases are stored as a dataset named `hr-regression-` followed by a code. Each item holds one question and its required facts, forbidden facts and source.
- **Experiments:** each run records one experiment on that dataset, named after the commit and the run number. Every case gets a score called `reference_checks`: 1 if both runs passed, 0 if not. Two experiments side by side show which cases changed between releases.

The test questions themselves also appear as normal traces, from the test accounts, so you can open any failing answer step by step.

**Where the result appears:** in Langfuse. Document 07 walks through each page.

## The production handoff job

It starts only after the `candidate` job succeeds. It checks two things: the tested commit is the one you merged, and the report says the gate passed. Then it prints what production would receive. It changes nothing.

**Next:** [06a2 Add the deployment jobs](06a2-add-deployment-jobs.md)
