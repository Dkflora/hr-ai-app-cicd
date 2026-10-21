# 07c Use case 3: missing retrieval evidence

**Goal:** see how answers change when the search stops returning one piece of evidence.

**OWASP LLM risk:** LLM08 Vector and embedding weaknesses, leading to LLM09 Misinformation. Missing evidence can produce an unsupported answer.

A PTO question can retrieve the carry-over rule without the annual entitlement, or the entitlement without the carry-over rule. `lambda/app/retrieval.py` runs two supplemental searches for PTO questions, one for each. You switch both off. Permissions stay exactly the same.

**This result depends on retrieval and the model.** The answer may give an unsupported number, fall back to a safe answer, or still be correct. If every case still passes, record that this change did not reproduce a failure. Do not edit the expected answers to force one.

## The code you change

```bash
cd ~/hr-rag-lab
grep -n -A7 'A PTO question can retrieve carryover alone' lambda/app/retrieval.py
```

The `if re.search(...)` line decides when to run the supplemental searches. You replace it with `if False:`, which never runs, and leave the indented block as it is.

## Step 1: Start from a clean, passing main

```bash
git switch main
git pull --ff-only
git status --short
git diff baseline --stat -- lambda/app/retrieval.py
```

**Expected:** both commands print nothing.

## Step 2: Switch off the supplemental searches

Create the branch and find the line:

```bash
git switch -c test/retrieval-evidence
grep -n -A1 'A PTO question can retrieve carryover alone' lambda/app/retrieval.py
grep -nF 'if re.search(r"\b(pto' lambda/app/retrieval.py
```

**Expected:** the first command prints the comment line, such as `97:`. The second prints two `if re.search(...)` lines, such as `101:` and `114:`. Change the first one only: it is the one just below the comment, indented by 4 spaces. The other belongs to the old-version search and stays as it is.

Make the change in VS Code:

1. Open `lambda/app/retrieval.py`.
2. Press **Ctrl+G**, type the first line number from the second command, such as `101`, and press **Enter**.
3. Replace the whole line with `    if False:`, keeping the 4 spaces at the start. Leave the indented lines below it unchanged.
4. Save the file with **Ctrl+S** (**Cmd+S** on a Mac).

Check the change before you commit:

```bash
git diff
```

**Expected:** one changed line. The old line starts `if re.search(r"\b(pto|time off|annual leave`; the new line is `if False:`.

```bash
git add lambda/app/retrieval.py
git commit -m "Exercise: disable the supplemental PTO searches"
git push -u origin test/retrieval-evidence
```

## Step 3: Merge and watch the run

1. Open a pull request from `test/retrieval-evidence` into `main`. The `checks` job passes.
2. Get review and merge.
3. Open the **new** run on `main`. Look at the PTO cases in the report, such as cases 7, 20, 24, 25 and 41, across both repetitions.

## Step 4: Inspect the trace

Sign in to the chatbot as Amara and ask these three questions in one conversation:

> How many PTO days do employees receive each year?

> How many of those can I carry over?

> What are the current rules?

In Langfuse, open each trace and its **Policy search** step. Its metadata lists `searches_run`: with the supplemental searches switched off, `supplemental annual entitlement` and `supplemental carryover` are missing. Then read the passages it returned. Compare the passages with the same questions in your baseline trace. Is the annual entitlement or the carry-over passage missing? Did the answer give a number the passages do not support?

## Step 5: Repair it

Restore the file exactly as it was at the baseline:

```bash
git switch main
git pull --ff-only
git switch -c fix/retrieval-evidence
git restore --source=baseline lambda/app/retrieval.py
git diff
```

**Expected:** one changed line, from `if False:` back to the `if re.search(...)` line.

```bash
git add lambda/app/retrieval.py
git commit -m "Restore the supplemental PTO searches"
git push -u origin fix/retrieval-evidence
```

Open a pull request, get review, merge, and confirm the newest `main` run passes.

## Step 6: Record what you saw

```bash
git switch main
git pull --ff-only
git branch -D test/retrieval-evidence fix/retrieval-evidence
```

Write down:

- Whether any case failed, and which ones.
- The search passages before and after, from the traces.
- Whether the repair brought the missing passage back.

**Next:** [08 Production handoff and rollback](08-production-handoff-and-rollback.md)
