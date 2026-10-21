# 07 Read the evaluation results

**Goal:** find each tool's result from your first run, and know what a pass or a failure tells you.

Document 06a explains what each tool is. This document reads the results.

## How the live API test decides

`ci/evaluate_api.py` asks every test question twice. For each answer it checks the expected facts, the forbidden facts, the cited source, and that the answer came from the exact release under test. A case passes only if **both** runs pass, and one failed run blocks approval. When it finishes, pass or fail, it deletes the test accounts' chats.

## What a failure means for each tool

- **Promptfoo** fails: a real regression in that case. Read the failing assertion in its log.
- **Langfuse** fails: scores dropped compared with the baseline experiment. Compare the two experiments to see which cases changed.
- **DeepEval** fails: compare the failing case's answer with its reference answer. The grader can be wrong, so read both before you decide.
- **Evidently** shows drift: answers got longer or slower than the reference run. Investigate the cause. It does not prove an answer is wrong.

## Where to find each result

- **Release gate and case counts**: Actions run → **Summary** → the report.
- **Promptfoo assertions**: Actions run → `candidate` job → **Promptfoo evaluation action** step log.
- **DeepEval pass or fail**: Actions run → `candidate` job → **Evaluate answer quality with DeepEval** step. Per-case scores go to `build/deepeval.json` on the runner, which the workflow does not upload.
- **Evidently report**: Actions run → **Artifacts** → download the Evidently report.
- **Langfuse**: the walkthrough below.

## Walk through your run in Langfuse

Open your Langfuse project and follow the pipeline's results in this order.

### 1. The prompt version

Open **Prompts → hr-policy-system**. The newest version is the one your run published, labelled `candidate`. Its config shows the commit it came from.

### 2. The dataset

Open **Datasets**, then the dataset whose name starts with `hr-regression-`. Its items are the test questions. Open one item to see the question with its required facts, forbidden facts and source. These items are the golden set from week 6, stored where every experiment can use them.

### 3. The experiment for your run

In that dataset, open the experiment runs. Each pipeline run adds one, named after its commit and run number. Open yours:

- Every item shows the captured answers and a `reference_checks` score: 1 if both runs passed, 0 if not.
- On a passing run, every score is 1.
- After a use case breaks something, open two runs side by side to see exactly which cases dropped to 0.

### 4. The traces behind one answer

Open **Traces** and set the time range to your run. The test questions appear as normal traces from the test accounts. Open one and read its spans in order: tool call, model call, inline judge, final answer. This is the same view as your first trace in document 03, so a failing case can be followed step by step.

## What the thresholds mean

- **Promptfoo at 100%** means every case in this fixed set passed on every run. It does not mean the chatbot answers every possible question correctly.
- **DeepEval at 0.7** is a demonstration threshold. A domain owner must review the rubric before using it as a production quality bar.
- **Evidently** compares distributions. The supplied reference is a synthetic failing run, so expect differences.

Keep the authorization and data-disclosure checks mandatory. When a case fails, investigate the answer or the grader. Never lower a threshold or edit an expected answer just to pass.

## Check your understanding

Open the report from your passing run and answer these:

1. How many cases passed every repetition, and how many application requests were recorded?
2. Pick case 2 from [the test cases](reference-test-cases.md). Which fact must the answer **not** contain, and why?
3. DeepEval grades only 3 cases with a model. What could it catch that the fact checks miss, and what could it get wrong?

**Next:** [07a Use case 1: tool-limit failure](07a-use-case-1-tool-limit-failure.md)
