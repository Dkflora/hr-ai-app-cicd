# 07c Use case 3: missing retrieval evidence

**Goal:** see how answers change when the search stops returning one piece of evidence.

**OWASP LLM risk:** LLM08 Vector and embedding weaknesses, leading to LLM09 Misinformation. Missing evidence can produce an unsupported answer.

A PTO carry-over question can retrieve the carry-over rule without the annual entitlement. `lambda/app/retrieval.py` runs a second, supplemental search for the annual entitlement. You switch that search off. Permissions stay exactly the same.

**This result depends on retrieval and the model.** The answer may give an unsupported number, fall back to a safe answer, or still be correct. If every case still passes, record that this change did not reproduce a failure. Do not edit the expected answers to force one.

## The code you change

```bash
cd ~/hr-rag-lab
grep -n -A7 'A PTO question can retrieve carryover alone' lambda/app/retrieval.py
```

The `if re.search(...)` line decides when to run the supplemental search. You replace it with `if False:`, which never runs, and leave the indented block as it is.

## Step 1: Start from a clean, passing main

```bash
git switch main
git pull --ff-only
git status --short
git diff baseline --stat -- lambda/app/retrieval.py
```

**Expected:** both commands print nothing.

## Step 2: Switch off the supplemental search

```bash
git switch -c test/retrieval-evidence
sed -i.bak 's/^    if re\.search(r"\\b(pto|time off|annual leave.*$/    if False:/' lambda/app/retrieval.py && rm lambda/app/retrieval.py.bak
git diff
```

**Expected:** one changed line. The old line starts `if re.search(r"\b(pto|time off|annual leave`; the new line is `if False:`.

```bash
git add lambda/app/retrieval.py
git commit -m "Exercise: disable the supplemental entitlement search"
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

In Langfuse, open each trace and read the **policy search** tool output. Compare the passages with the same questions in your baseline trace. Is the annual entitlement passage missing? Did the answer give a number the passages do not support?

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
git commit -m "Restore the supplemental entitlement search"
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
