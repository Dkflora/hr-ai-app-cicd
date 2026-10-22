# 06a How the deployment jobs work

**Goal:** understand what the deployment jobs do, before you add them to your workflow in documents 06a2 and 06a3.

There is nothing to run in this document.

## The big picture

Every merge to `main` starts the same chain of jobs. In plain words:

1. **Check** the code: run the tests and build it. This is the `checks` job from document 04.
2. **Deploy** the new version to **staging**. Staging is the company's test copy of the app, separate from production. The engineers, the HR expert who reviews the answers, and the pipeline all use it before a version is approved.
3. **Test** the deployed app by asking it real questions, the way an employee would.
4. **Decide:** if every test passed, mark this version as **approved**. If any test failed, stop. A failing version is never approved.
5. **Report** what happened, pass or fail.
6. **Hand off** to production. In this lab, this last job only prints what production would receive.

Step 4 is called the **release gate**: the point where one failed test stops the release. Steps 2 to 5 run in the `candidate` job. Step 6 is the `production-handoff-dry-run` job.

## How a version is deployed: Lambda versions and aliases

The app's backend runs on AWS Lambda. Lambda keeps every release as a separate, numbered copy:

- **Version:** a numbered copy of the code and its settings, such as version 7 or 8. Once created, a version never changes.
- **Alias:** a name that points to one version. You can move it to point at another version. The app is always called through the alias name. So moving the alias switches everyone to the new version at once.

If you know Git: versions are like commits, and aliases are like branches.

The chat function has two aliases:

- **`candidate`** points to the newest version, the one being tested. The pipeline moves it on every merge. The staging app you sign in to uses it.
- **`approved`** points to the last version that passed every test. The pipeline moves it only when the release gate passes.

So when a merge breaks something, `candidate` points to the broken version, and `approved` still points to the last good one. The staging app shows the broken answers, because it follows `candidate`. Documents 07a to 07c use this to show a failure safely.

Right now the chat function has only `candidate`. The first passing run, in document 06b, creates `approved`.

## What the candidate job does, in order

Each item below is one step in the workflow file, with the script or action it runs.

**Before it starts**
- **Runs only on `main`, and only after `checks` passed.** A pull request never gets AWS access or secrets. So code that has not been reviewed cannot touch AWS.

**Sign in and deploy**
- **Sign in to AWS** (`configure-aws-credentials`): uses the role from document 05. AWS gives the job temporary credentials that expire within the hour.
- **Deploy the website** (`ci/deploy_frontend.py`): builds the React website from this commit and uploads it.
- **Publish the prompt** (`ci/release.py --publish`): saves the system prompt in Langfuse as a numbered version, linked to this commit.
- **Deploy the backend** (`ci/deploy_candidate.py`): uploads the code as a new Lambda version, and moves `candidate` to it.

**Test**
- **Ask the real app**, also called the **API test** (`ci/evaluate_api.py`): signs in as the test accounts and asks one warm-up question that is not timed. Then it asks every question in [the test cases](reference-test-cases.md) twice. A wrong answer, or an answer slower than 20 seconds, fails the step.
- **Check retrieval and consistency** (`ci/quality_checks.py`): checks that the search finds each case's expected policy, and that both answers to each question say the same thing.

**Evaluate the answers**
- **Langfuse, Promptfoo, DeepEval and Evidently** each score the saved answers in their own way. The next section explains each one.

**Decide and report**
- **Approve** (`ci/promote_lab.py`): moves `approved` to this version, but only if every step above passed.
- **Report** (`ci/report.py`): writes a summary on the run page and on the pull request. It never includes employees' answers.

If the API test (**Ask the real app**) fails, Langfuse, Promptfoo, Evidently and the report still run, so you can see what broke. **Approve** is skipped, and so is DeepEval.

## The answers file: build/evaluation.json

The API test saves every answer it gets in one file, `build/evaluation.json`, on GitHub's machine. For each of the 104 answers it records:

- Which test case it was, and whether this was the first or second try.
- The full answer and the policy sources it cited.
- How long it took.
- Whether it passed, and if not, why, such as `missing:5` or `slow:22.1s`.

Every later check reads this file instead of asking the app again: retrieval and consistency, Promptfoo, DeepEval, Langfuse, Evidently, the approval step and the report. So every tool judges the same answers, and the model is asked only once per answer.

The file holds full answers, including the test accounts' salary figures. So it is never uploaded with the run's files. It disappears when the job ends. Only the summary and the score files are kept.

## What is checked, and by which tool

Every check below reads the answers the live test saved. None of them asks the app again.

- **Facts, privacy, sources, scope, attacks, versions, follow-ups, personal data:** the live test and Promptfoo check these on every case. The test case groups show which cases cover what.
- **Fairness:** cases 46 to 48 ask the same policy questions as a manager, an HR person and an executive. The policy answer should be the same for every role.
- **Robustness:** cases 49 to 51 ask the same questions with typos or in other words.
- **Toxicity:** case 52 asks for an insult. The assistant must refuse.
- **Speed:** every answer must arrive within 20 seconds, after one warm-up question. The limit is set in `ci/evaluate_api.py`.
- **Retrieval quality** and **consistency:** `ci/quality_checks.py` checks these on the 14 cases that name an expected policy.
- **Faithfulness, relevance, bias and toxicity of the wording:** DeepEval checks these on 5 of those 14 cases.
- **Drift:** Evidently writes a report.
- **History across releases:** the Langfuse experiment.

The checks that follow fixed rules decide the release. They cost little, give the same result every time, and never disagree with themselves. Checks where a model grades the answer add extra evidence on a sample. A grading model costs money and can be wrong, so it only checks a few answers.

### Retrieval quality and consistency

**What it tests here:** two things. No model grades anything.

- **Retrieval quality:** retrieval is the search that finds policy passages for a question. For each of the 14 cases with an expected policy, the search runs again as that case's test account. The expected policy must be among the passages it returns. The report shows the **hit rate**: the share of cases whose policy was found. It also shows the **mean reciprocal rank**: how high the policy came in the results. It is 1 when the policy always comes first, and 0.5 when it always comes second.
- **Consistency:** both answers to each policy question are turned into lists of numbers that capture their meaning, called **embeddings**, using the app's own embedding model. Then the two are compared. Their similarity must be at least 0.75, set as `MIN_CONSISTENCY` in `ci/quality_checks.py`. Refusals are left out: two correct refusals in different words score low, and the fact checks already make sure both runs refuse. In a test, a reworded answer scored 0.87 and an unrelated answer scored 0.07.

**Where the result appears:** the log of the **Check retrieval quality and answer consistency** step, and the run's report.

### Promptfoo: the fact checks

**What it is:** an open-source tool that tests the output of an AI model against written rules. Teams often run it in CI.

**What it tests here:** every answer, from both runs of every case, against that case's rules in [the test cases](reference-test-cases.md):

- It contains every **required fact**, such as `5` for the carry-over question.
- It contains none of the **forbidden facts**, such as another employee's salary.
- It names the expected policy as its **source**.

Upper and lower case do not matter, and neither do commas, `$` or `*`. The threshold is 100%: one broken rule fails the step. Promptfoo repeats the live API test's checks with a standard tool whose results anyone can read.

**Where the result appears:** the log of the **Promptfoo evaluation action** step in the run.

### DeepEval: a model grades the answer

**What it is:** an open-source framework for **LLM-as-a-judge**. A second AI model reads an answer and scores it against written rules, called a rubric.

**What it tests here:** 5 of the 52 test cases. `ci/deepeval_check.py` picks them from the saved answers, with a fixed rule:

1. Keep only the 14 cases that name an expected policy. Faithfulness needs the policy text the answer was built from. Refusals, small talk and attacks have none.
2. Walk those cases in file order, and take the first case of each group. The 14 cases belong to 5 groups, so this gives exactly 5.

So every run grades the same five cases, as numbered in [the test cases](reference-test-cases.md): 6 (everyday), 11 (access), 18 (version), 46 (fairness) and 49 (robustness). DeepEval grades the first answer of each. Because the five never change, a score that drops between releases means the release changed, not the sample. If one of the five gets no answer, the next case of its group takes its place.

Why only 5: each case gets five scores, and each score takes several calls to the grading model. That adds minutes and cost to every run. The other cases are still fully checked by the live test and Promptfoo. The number is `SAMPLE_SIZE` in `ci/deepeval_check.py`. Set the `DEEPEVAL_DEMO_CASES` variable to grade more.

**How to read a score:** each check gives the answer a number from 0 to 1. 1 means the answer fully meets the rule, and 0 means not at all. For example, a faithfulness score of 0.8 means 8 out of 10 claims in the answer agree with the policy text the search returned. The **pass mark** is the lowest score that still passes. Here it is 0.7 for every check, set as `PASS_MARK` in `ci/deepeval_check.py`.

Each answer gets five scores:

- **HR reference outcome:** a rubric written for this lab. It lowers the score when a required fact is missing or a forbidden fact appears. It accepts a refusal when the case requires one. It also accepts an answer that corrects a false claim. Pass mark 0.7.
- **Faithfulness:** every claim in the answer must be backed by the passages the search returned. This checks for invented facts, often called hallucinations. Pass mark 0.7.
- **Answer relevancy:** the answer must address the question that was asked. Pass mark 0.7.
- **Bias** and **Toxicity:** the share of statements free of bias or toxic language. 1.0 means none was found. Pass mark 0.7.

A grading model can be wrong, so DeepEval only adds a second opinion. It never replaces the fact checks.

**Where the result appears:** the log of the **Evaluate answer quality with DeepEval** step.

### Evidently: drift

**What it is:** an open-source tool that compares new data with older reference data, and reports what changed. A change like this is called **drift**.

**What it tests here:** two numbers for each answer, its length and its response time. It compares them with a reference run saved in the repository, `ci/data/drift-reference.json`. It only reports; it never fails the run. A change is a reason to look at the answers, not proof that one is wrong.

**Where the result appears:** in the run's **Artifacts**, as an HTML report.

### Langfuse: traces, prompts and experiments

You met Langfuse traces in document 03. The pipeline uses three more Langfuse features:

- **Prompts:** each run saves the system prompt as a new numbered version of `hr-policy-system`. The version is labelled `candidate` and tagged with the commit. Every trace links to the prompt version that produced it.
- **Datasets:** the test cases are saved as a dataset. Its name is `hr-regression-` followed by the first 16 characters of a fingerprint of the test cases. When the test cases change, the name changes, so old and new cases never mix. Each item holds one question, with its required facts, forbidden facts and source.
- **Experiments:** each run records one experiment on that dataset, named after the commit and the run number. Every case gets a score called `reference_checks`: 1 if both runs passed, 0 if not. Put two experiments side by side to see which cases changed between releases.

The test questions also appear as normal traces from the test accounts. So you can open any failing answer and follow it step by step.

**Where the result appears:** in Langfuse. Document 07 walks you through each page.

## One release number everywhere

The `VERSION` file holds the release number, such as `1.0.3`. Each change raises it: the last number for a fix, the middle number for a new feature, the first number for a change that breaks something. This is called **semantic versioning**. The pipeline stamps the number on everything it builds, so each place shows which release it belongs to:

- **The package:** `release.json` records the version, the commit and the prompt.
- **Langfuse prompt:** the prompt version gets the label `v1.0.3`, next to `candidate`.
- **Lambda:** the published version's description reads `v1.0.3 (commit a21bc86)`. AWS still numbers versions 1, 2, 3, and the description says which release each one is.
- **Traces:** every trace's **Release** field shows `v1.0.3`.
- **API answers:** each answer carries the header `x-hr-release: v1.0.3`.
- **Git:** after the release gate passes, the `tag-release` job tags the tested commit `v1.0.3` and pushes the tag to GitHub. A release that fails the gate gets no tag.

## What these checks still do not cover

Every gate has blind spots. Knowing them is part of running it:

- **Real users:** the test cases are a fixed list. Real people can ask things no case covers. Their thumbs up and down reach Langfuse as scores, but those scores only point to answers to review. They do not stop a release.
- **Full reference answers:** each case lists required facts, not a complete ideal answer. So nothing compares a whole answer with an ideal one.
- **Human review:** the grading model's scores have not yet been compared with an HR expert's grades on the same answers.
- **Wider attacks:** there are five attack cases, but no systematic attack testing, called red-teaming.
- **Load:** the tests ask one question at a time, never many people at once.

## The production handoff job

This job starts only after the `candidate` job succeeds. It checks two things: the tested commit is the one you merged, and the report says the gate passed. Then it prints what production would receive. It changes nothing.

**Next:** [06a2 Add the deployment jobs](06a2-add-deployment-jobs.md)
