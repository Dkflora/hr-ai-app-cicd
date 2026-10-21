# 07c Use case 3: missing retrieval evidence

**Goal:** see how answers change when the search stops finding one piece of the policy.

**OWASP LLM risk:** LLM08 Vector and embedding weaknesses, leading to LLM09 Misinformation. When evidence is missing, the model can give an answer the policy does not support.

**Retrieval** is the step where the app searches the policy documents and hands the matching passages to the model. The model should answer only from those passages.

A PTO question can find the carry-over rule without the yearly allowance (the annual entitlement). It can also find the yearly allowance without the carry-over rule. To avoid that, `lambda/app/retrieval.py` runs two extra searches for every PTO question, one for each. These are the **supplemental searches**. In this use case you switch both off. Who may read which document stays exactly the same.

**The result depends on the search and the model.** The answer may give a number the policy does not support. It may fall back to a safe reply. Or it may still be correct. If every case still passes, that is a valid result too. Write down that this change did not cause a failure.

## The code you change

```bash
cd ~/hr-rag-lab
grep -n -A7 'A PTO question can retrieve carryover alone' lambda/app/retrieval.py
```

The `if re.search(...)` line decides when the supplemental searches run. You replace it with `if False:`. A block under `if False:` never runs. You leave the indented lines below it as they are.

## Step 1: Start from a clean, passing main

```bash
git switch main
git pull --ff-only
git status --short
git diff v1.0.0 --stat -- lambda/app/retrieval.py
```

**Expected:** both commands print nothing.

## Step 2: Switch off the supplemental searches

Create the branch and find the line:

```bash
git switch -c test/retrieval-evidence
grep -n -A1 'A PTO question can retrieve carryover alone' lambda/app/retrieval.py
grep -nF 'if re.search(r"\b(pto' lambda/app/retrieval.py
```

**Expected:** the first command prints the comment line, such as `97:`. The second prints two `if re.search(...)` lines, such as `101:` and `114:`.

Change the first one only. It is the line just below the comment, indented by 4 spaces. The other one belongs to the search for old policy versions. Leave it as it is.

Make the change in VS Code:

1. Open `lambda/app/retrieval.py`.
2. Press **Ctrl+G**, type the first line number from the second command, such as `101`, and press **Enter**.
3. Replace the whole line with `    if False:`, keeping the 4 spaces at the start. Leave the indented lines below it unchanged.
4. Save the file with **Ctrl+S** (**Cmd+S** on a Mac).

Check the change before you commit:

```bash
git diff
```

**Expected:** one changed line. The old line starts `if re.search(r"\b(pto|time off|annual leave`. The new line is `if False:`.

```bash
git add lambda/app/retrieval.py
git commit -m "Exercise: disable the supplemental PTO searches"
git push -u origin test/retrieval-evidence
```

## Step 3: Merge and watch the run

1. Open a pull request from `test/retrieval-evidence` into `main`. The `checks` job passes.
2. Get it reviewed and merge it.
3. In GitHub, open the **Actions** tab and click the **new** run on `main`. In the report, look at the PTO cases, such as cases 7, 20, 24, 25 and 41. Check both runs of each case.

## Step 4: Inspect the trace

Sign in to the chatbot as Amara. Ask these three questions in one conversation:

> How many PTO days do employees receive each year?

> How many of those can I carry over?

> What are the current rules?

In Langfuse, open the trace for each question. Click its **Policy search** step and look at the metadata:

- `searches_run` lists the searches that ran. With your change, `supplemental annual entitlement` and `supplemental carryover` are missing.
- The passages show the policy text the model received.

Compare these passages with the same questions in the trace from your `v1.0.0` run. Is the yearly allowance or the carry-over passage missing? Did the answer give a number that the passages do not support?

## Step 5: Repair it

Put the file back exactly as it was in release `v1.0.0`:

```bash
git switch main
git pull --ff-only
git switch -c fix/retrieval-evidence
git restore --source=v1.0.0 lambda/app/retrieval.py
git diff
```

**Expected:** one changed line, from `if False:` back to the `if re.search(...)` line.

```bash
git add lambda/app/retrieval.py
git commit -m "Restore the supplemental PTO searches"
git push -u origin fix/retrieval-evidence
```

Open a pull request, get it reviewed, and merge it. Then check that the newest run on `main` passes.

## Step 6: Record what you saw

```bash
git switch main
git pull --ff-only
git tag -a v1.0.3 -m "Restore the supplemental PTO searches"
git push origin v1.0.3
git branch -D test/retrieval-evidence fix/retrieval-evidence
```

The repair passed every check, so it is the next patch release, `v1.0.3`.

Write down:

- Whether any case failed, and which ones.
- The search passages before and after, from the traces.
- Whether the repair brought the missing passage back.

**Next:** [08 Production handoff and rollback](08-production-handoff-and-rollback.md)
