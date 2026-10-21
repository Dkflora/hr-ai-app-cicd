# 07a Use case 1: tool-limit failure

**Goal:** prove the release gate blocks a broken change that passes every static check.

**OWASP LLM risk:** LLM06 Excessive agency and LLM10 Unbounded consumption. The tool limit stops the agent from looping without end.

You reduce the agent's tool budget from 5 rounds to 1. The code still compiles and the unit tests still pass, so the pull request looks fine. After the merge, the live API test fails and the `approved` pointer stays on the baseline. You then repair it with a second pull request.

This use case fails the same way every time, so run it first.

## How the tool loop works

`lambda/app/assistant.py` gives the model up to `MAX_TOOL_ROUNDS` turns. On the first turn the model must call a tool, such as policy search. The next turn writes the answer from what the tool returned.

With one round, the policy search uses the only turn. No turn is left to write the answer, so the employee gets: `Sorry, I couldn't finish that answer. Please try again.`

## Branches in this use case

- `test/tool-limit` sets `MAX_TOOL_ROUNDS = 1`. After merge: live test fails, approval blocked.
- `fix/tool-limit` sets `MAX_TOOL_ROUNDS = 5`. After merge: live test passes, approval moves.

Both start from the latest `main` and return to `main` through their own pull request.

## Step 1: Start from a clean, passing main

```bash
cd ~/hr-rag-lab
git switch main
git pull --ff-only
git status --short
grep -n '^MAX_TOOL_ROUNDS' lambda/app/assistant.py
```

**Expected:** `git status --short` prints nothing, and the last line is `58:MAX_TOOL_ROUNDS = 5`.

Before breaking anything, write down three things from your passing run: the commit, the prompt version, and the Lambda version the `approved` alias points to. Print the alias:

```bash
aws lambda get-alias \
  --function-name "$(terraform -chdir=infra/terraform output -raw candidate_function)" \
  --name approved \
  --query FunctionVersion --output text
```

## Step 2: Break it

```bash
git switch -c test/tool-limit
sed -i.bak 's/^MAX_TOOL_ROUNDS = 5$/MAX_TOOL_ROUNDS = 1/' lambda/app/assistant.py && rm lambda/app/assistant.py.bak
git diff
```

**Expected:** the diff shows exactly one changed line, from `5` to `1`.

```bash
git add lambda/app/assistant.py
git commit -m "Exercise: limit the agent to one tool round"
git push -u origin test/tool-limit
```

## Step 3: Open the pull request and merge it

1. In GitHub, open a pull request from `test/tool-limit` into `main`.
2. Watch the `checks` job. **It passes**, because the code is still valid.
3. Get reviewer approval and merge.

You merge on purpose. This is an authorized fault test in synthetic staging. Never do this to a live production branch.

## Step 4: Watch the gate block the release

Open **Actions** and select the **new** run on `main`.

**Expected:**

- `Test the real authenticated application` fails.
- Promptfoo shows failed assertions.
- `Approve the exact tested staging version` is **skipped**.
- The report says `Release gate: FAIL.`.
- `Production handoff (dry run)` is **skipped**.

The pull request is already merged. The **release** is what the gate blocked.

Confirm the `approved` alias did not move:

```bash
aws lambda get-alias \
  --function-name "$(terraform -chdir=infra/terraform output -raw candidate_function)" \
  --name approved \
  --query FunctionVersion --output text
```

**Expected:** the same version number you wrote down in step 1.

## Step 5: Inspect the cause in Langfuse

Sign in to the chatbot as Amara and ask:

> How many PTO days do employees receive each year?

The staging UI uses the `candidate` alias, so it shows the broken answer even though the release is blocked.

In Langfuse, open that trace. You should see the policy search tool span, and then no second model turn. The answer is the safe "couldn't finish" message.

To see the same thing from the gateway, open the admin UI as in document 03, step 5. In **Logs**, compare this question's model calls with the same question from your passing run.

## Step 6: Repair it with a new branch

The broken change is already in `main`, so the repair needs its own branch and pull request.

```bash
git switch main
git pull --ff-only
git switch -c fix/tool-limit
sed -i.bak 's/^MAX_TOOL_ROUNDS = 1$/MAX_TOOL_ROUNDS = 5/' lambda/app/assistant.py && rm lambda/app/assistant.py.bak
git diff
```

**Expected:** one changed line, from `1` back to `5`.

```bash
git add lambda/app/assistant.py
git commit -m "Restore the working tool budget"
git push -u origin fix/tool-limit
```

Open a pull request from `fix/tool-limit` into `main`, get review, and merge.

## Step 7: Confirm the repair

Open the **newest** run on `main`.

**Expected:** every job green, the report says `Release gate: PASS.`, and the `approved` alias moves to the new version:

```bash
aws lambda get-alias \
  --function-name "$(terraform -chdir=infra/terraform output -raw candidate_function)" \
  --name approved \
  --query FunctionVersion --output text
```

Ask the same PTO question again. In Langfuse, the fixed trace shows: policy search, a model turn after it, the inline judge, then the final answer.

If an unrelated case fails, investigate it. Do not change the expected answers.

## Step 8: Clean up the branches

```bash
git switch main
git pull --ff-only
git branch -D test/tool-limit fix/tool-limit
```

## Evidence to keep

- The bad commit and the fix commit.
- The failing run link and the passing run link.
- The two Langfuse trace links for the PTO question, before and after.
- The `approved` version before, during and after.

**Next:** [07b Use case 2: wrong prompt instruction](07b-use-case-2-wrong-prompt-instruction.md)
