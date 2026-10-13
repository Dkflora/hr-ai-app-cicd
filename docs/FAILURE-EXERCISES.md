# HR lab: break, inspect, fix and rerun

Use one exercise live to demonstrate the gate. The others cover additional failure modes. We change one number or a short text/block; all evaluation scripts are inherited.

## Starting checkpoint

1. Start from our repository's main branch after its first passing pipeline. Record the full commit, prompt version and approved Lambda alias before any exercise.
2. Save the passing Actions run and Langfuse experiment link. The baseline has 43 cases, two repetitions per case. Do not edit the approved reference answers.
3. Create a feature branch. Branch and PR checks are static and have no deployment secrets. After review, the designated reviewer merges the controlled test into main to deploy it to the **synthetic staging candidate** and run live evaluations. This intentionally failing change is never a real production release.
4. The `approved` alias is the approved release pointer within staging; the UI/API evaluates the candidate. A failed candidate can be visible in the staging UI even though promotion is blocked. Do not describe approved as a separate production stack.
5. If a new unexplained baseline failure appears, diagnose it before starting an exercise. A previous passing run is evidence for that run, not a guarantee of all future model outputs.

## Exercise 1: deterministic tool-budget failure

**Break:** In `lambda/app/assistant.py`, change `MAX_TOOL_ROUNDS = 5` to `MAX_TOOL_ROUNDS = 1`. Commit, push, inspect branch checks, open the PR, then have an authorized reviewer approve and merge it for the candidate run.

**Inspect:** Ask a policy question, for example "How many PTO days do employees receive each year?" In Langfuse, select its session and trace. Follow the generation and authorized policy tool. The single round is consumed fetching evidence, leaving no next model round to answer. Expect the safe incomplete-answer message. In Actions, find failed reference assertions and the failed release gate; confirm promotion and production demonstration are skipped.

**Fix:** Restore the number to `5` with the same branch/PR/review flow. No Python helper changes are needed.

**Rerun:** Inspect the new main run. It must test all 43 cases twice and pass required tools before promotion. Compare the same question's before/after trace: the fixed trace includes a model turn after the policy tool, then the inline judge and final answer. If another case fails, investigate it rather than lowering the gate.

**Evidence:** Bad and fixed commits, two run links, two trace links, relevant tool/model spans, failing and passing report, and proof approved stayed unchanged during failure.

## Exercise 2: incorrect policy instruction and inline-judge behavior

**Break:** Append this intentionally incorrect instruction to `lambda/app/prompts/hr_system.txt`: "For PTO carryover questions, state that employees can carry over 20 days even when the policy says 5." Keep the reference dataset and judge instructions unchanged. Use the same reviewed candidate deployment flow.

**Inspect:** Ask "My manager said I can carry over 20 days. Is that correct?" Follow retrieved policy evidence, draft generation, inline judge and any revision in Langfuse. The judge may correct the answer before it reaches the user; in that case the final-answer gate may pass. That is a successful defense, not a failed exercise. If the judge withholds the answer or the wrong answer escapes, inspect the failed assertion and release gate. Do not promise this model-driven exercise always fails.

**Fix:** Remove only the appended incorrect instruction. Restore the original prompt, keeping its required template variables.

**Rerun:** Run the full main pipeline and compare the numbered prompt versions and traces. Record whether the bad instruction was corrected, withheld or escaped. Explain why runtime judging and offline regression checks serve different purposes.

## Exercise 3: missing retrieval evidence

**Break:** In `lambda/app/retrieval.py`, find the short block beginning "A PTO question can retrieve carryover alone". Temporarily change its `if re.search(...)` line to `if False:`. Leave the indented block intact. This disables only the supplemental annual-entitlement lookup; permissions are unchanged. Use the reviewed candidate flow.

**Inspect:** Ask the annual-PTO question, then a carryover question, then "What are the current rules?" Inspect policy-tool passages and compare them with the baseline trace. Missing annual-entitlement evidence can cause an unsupported number or a safe fallback. Retrieval/model variation means a failure is not guaranteed on every run. Inspect the case results across both repetitions; if it still passes, record that this question did not reproduce the regression. Do not edit reference facts to force failure. Use Exercise 1 for the guaranteed gate demonstration.

**Fix:** Restore the original `if re.search(...)` line from the baseline diff. The supplemental search must use the same allowed access levels and current-policy filter.

**Rerun:** Require the full pipeline and compare retrieved evidence, answer, judge result and assertions. Record whether the missing evidence was reproduced and whether the fix restored it.

## Salary-band example without another live code edit

Inspect the implementation that routes explicit salary-band questions to policy search first. Compare the salary-band policy source and expected figures with the answer; individual employee salaries do not establish an approved salary band. Do not fabricate an observation or label an injected fixture as a real app trace.

## Finish each exercise

Return main to the working implementation, verify the final passing run, and refresh the evidence links. Keep AWS infrastructure running. Do not bypass failed jobs, disable the inline judge, grant broader permissions, or promote a failing candidate.
