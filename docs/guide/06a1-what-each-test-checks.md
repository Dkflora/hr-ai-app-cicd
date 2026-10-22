# 06a1 What each test checks

**Goal:** know what each check in the `candidate` job looks at, which questions it uses and why, and how it passes. This is reading only.

Every check below works on the [test cases](reference-test-cases.md): questions with known correct answers, in `lambda/data/evaluation_questions.json`. The first check asks the app those questions and saves the answers in `build/evaluation.json`, the answers file from document 06a. Every other check reads that file. None of them asks the app again.

Each section answers the same questions:

- **What it is**
- **What it checks**
- **Which questions, and why**
- **How it passes**
- **Where to see the result**

Numbers below, such as case numbers, come from the current test cases. They change when the test cases change.

## What the test cases cover

Each test case belongs to a **group**, which says what it tests. For example, with the current test cases:

- **Everyday, access, version, country, follow-up, false claim, attack, personal data, out of scope, small talk:** facts, privacy, sources and scope. [The test cases](reference-test-cases.md) list each group's cases.
- **Fairness:** cases 46 to 48 ask the same policy questions as a manager, an HR person and an executive. The policy answer should be the same for every role.
- **Robustness:** cases 49 to 51 ask the same questions with typos or in other words.
- **Toxicity:** case 52 asks for an insult. The assistant must refuse.

## Live API test

**What it is:** `ci/evaluate_api.py`, a Python script written for this lab. It uses the staging app the way a person does: it signs in to Cognito as a test account and sends each question to the app's API.

**What it checks:** each answer must:

- Contain every **required fact**, such as `5` for the carry-over question.
- Contain none of the **forbidden facts**, such as another employee's salary.
- Name the expected policy as its **source**, when the case has one.
- Arrive within the time limit.
- Come from the version under test, shown by the answer's `x-hr-release` and `x-hr-commit` headers.

It also checks that a question sent without signing in is refused.

**Which questions, and why:** every test case, asked twice. The AI model can word an answer differently each time, so one good answer could be luck. Before the timed questions, it asks one warm-up question that is not checked, so a search index that has been idle does not count against the first case.

**How it passes:** every answer passes every rule. One broken rule fails the step. The number of tries is `EVAL_REPEATS` and the time limit is `EVAL_MAX_LATENCY_SECONDS`, both in `ci/evaluate_api.py`, 2 tries and 20 seconds by default.

**Where to see the result:** the log of the **Test the real authenticated application** step, and the totals in the run's report.

## Retrieval quality

**What it is:** the first half of `ci/quality_checks.py`. Retrieval is the search that finds policy passages for a question. No model grades anything here.

**What it checks:** whether the search returns the expected policy, and how high in the results.

**Which questions, and why:** only cases that name an expected policy as their source. The other cases, such as refusals and small talk, have no policy to find. The search runs again as each case's test account, so it sees only the documents that role may read.

**How it passes:** every one of these cases must find its expected policy. The report also shows two numbers, for information:

- **Hit rate:** the share of cases whose policy was found.
- **Mean reciprocal rank:** how high the policy came. It is 1 when the policy always comes first, and 0.5 when it always comes second.

**Where to see the result:** the log of the **Check retrieval quality and answer consistency** step, and the run's report.

## Answer consistency

**What it is:** the second half of `ci/quality_checks.py`. It turns each answer into a list of numbers that capture its meaning, called an **embedding**, with the app's own embedding model, Amazon Titan. Then it compares two answers.

**What it checks:** whether the two answers to the same question mean the same thing. An employee who asks twice should get the same policy answer.

**Which questions, and why:** only cases that name an expected policy, using both of their answers. Refusals are left out: two correct refusals in different words can score low, and the live test already makes sure both answers refuse.

**How it passes:** the two answers' similarity must be at least 0.75, set as `MIN_CONSISTENCY` in `ci/quality_checks.py`. In a test, a reworded answer scored 0.87 and an unrelated answer scored 0.07.

**Where to see the result:** the same step's log, and the run's report.

## Promptfoo

**What it is:** an open-source tool that tests the output of an AI model against written rules. Teams often run it in CI. Here it uses no model: each rule is a short JavaScript check.

**What it checks:** the same content rules as the live API test: required facts, forbidden facts and the source. Upper and lower case do not matter, and neither do commas, `$` or `*`.

**Which questions, and why:** every test case, with both of its answers. It repeats the live test's content checks with a standard tool, whose results anyone on the team can read.

**How it passes:** 100% of the cases pass, set by `fail-on-threshold` in the workflow. One broken rule fails the step.

**Where to see the result:** the log of the **Promptfoo evaluation action** step. There, `case_id` counts from 0, so `case_id` 40 is case 41 in the test cases.

## DeepEval

**What it is:** an open-source framework for **LLM-as-a-judge**. A second AI model, the judge, reads an answer and scores it against written rules, called a rubric. The judge here is Amazon Nova Pro, reached through the evaluation Lambda and the model gateway.

**What it checks:** five things in each answer.

- **HR reference outcome:** a rubric written for this lab. The answer must contain the required facts and none of the forbidden ones. A refusal is right when the case asks for one, and so is correcting a false claim.
- **Faithfulness:** every claim must agree with the policy passages the search returned. This catches invented facts, often called hallucinations.
- **Answer relevancy:** the answer must address the question that was asked.
- **Bias** and **Toxicity:** the share of statements free of bias or toxic language.

**Which questions, and why:** you can give DeepEval any set of test cases. Each case costs several calls to the judge, so this lab grades a small sample, 5 cases by default. The sample keeps only cases whose answer should cite a policy, because faithfulness needs that policy text. `ci/deepeval_check.py` then takes the first such case of each group, in file order. If it still needs more, it adds the next cases. It grades the first answer of each case.

For example, with the current test cases it grades cases 6, 11, 18, 46 and 49. Cases 46 and 49 re-ask case 6, as a manager and with typos. There is no randomness, so the same test cases always give the same sample, and a score change means the release changed. To grade more, raise `SAMPLE_SIZE` in `ci/deepeval_check.py`, or set the `DEEPEVAL_DEMO_CASES` variable.

**How it passes:** each check gives a **score** from 0 to 1. 1 means the answer fully meets the rule, and 0 means not at all. For example, a faithfulness score of 0.8 means 8 out of 10 claims agree with the policy text. Every score must reach the **pass mark**, 0.7, set as `PASS_MARK` in `ci/deepeval_check.py`. A judge can be wrong, so DeepEval adds a second opinion and never replaces the fact checks. It runs only when the `ENABLE_DEEPEVAL` variable is `true`.

**Where to see the result:** the log of the **Evaluate answer quality with DeepEval** step, the run's report, and `deepeval.json` in the run's `hr-candidate-evidence` files.

## Evidently

**What it is:** an open-source tool that compares new data with older reference data, and reports what changed. A change like this is called **drift**.

**What it checks:** two numbers for each answer: its length and its response time. It never reads the answer text.

**Which questions, and why:** every answer from this run, compared with the answers of a passing run saved in the repository, `ci/data/drift-reference.csv`. A sudden change in length or speed is a reason to look at the answers, even when every test passed.

**How it passes:** it never fails on drift. It only writes a report. The step before it does stop the run if the reference was built from different test cases than today's. A unit test catches that earlier, on the pull request. It runs only when the `ENABLE_EVIDENTLY` variable is `true`.

**Where to see the result:** on the run page, under **Artifacts**, download `evidently-results` and open the HTML report.

## Langfuse experiment

**What it is:** `ci/langfuse_experiment.py`, run by Langfuse's GitHub Action. It records each run in Langfuse, so releases can be compared side by side.

**What it checks:** for each test case, whether both of its answers passed. It saves that as a score called `reference_checks`: 1 if both passed, 0 if not.

**Which questions, and why:** every test case. They are saved in Langfuse as a dataset named `hr-regression-` plus the first 16 characters of a fingerprint of the test cases. When the test cases change, the name changes, so old and new cases never mix.

**How it passes:** every case scores 1. Any 0 fails the step.

**Where to see the result:** in Langfuse, under **Datasets**. Document 07 walks you through it.

## Which checks decide the release

The approval step runs only when every step before it passed. So a failure in the live test, retrieval, consistency, Promptfoo, DeepEval or the Langfuse experiment stops the release. Evidently only reports.

The checks that follow fixed rules cost little and give the same result every time. The judge model costs money and can be wrong, so it only adds evidence on a sample.

**Next:** [06a2 Add the deployment jobs](06a2-add-deployment-jobs.md)
