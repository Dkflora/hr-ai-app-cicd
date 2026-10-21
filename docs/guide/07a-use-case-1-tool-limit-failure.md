# 07a Use case 1: tool-limit failure

**Goal:** prove that the pipeline stops a broken change from being approved, even when every code check passes.

**OWASP LLM risk:** LLM06 Excessive agency and LLM10 Unbounded consumption. A limit on tool rounds stops the assistant from looping forever.

In this use case you break the assistant on purpose. A **tool round** is one turn where the model asks for a tool, such as the policy search, and reads the result. The assistant normally gets 5 rounds. You cut it to 1.

The code still runs and the unit tests still pass, so the pull request looks fine. After you merge it, the test that asks the real app questions fails. The `approved` pointer stays on the last good version. Then you repair the change with a second pull request.

This use case fails the same way every time, so run it first.

## How the tool loop works

`lambda/app/assistant.py` gives the model up to `MAX_TOOL_ROUNDS` turns. On the first turn, the model must call a tool, such as the policy search. On the next turn, it writes the answer from what the tool returned.

With only one round, the policy search uses up that one turn. No turn is left to write the answer. So the employee gets this message: `Sorry, I couldn't finish that answer. Please try again.`

## Branches in this use case

- `test/tool-limit` sets `MAX_TOOL_ROUNDS = 1`. After you merge it, the live test fails and the version is not approved.
- `fix/tool-limit` sets `MAX_TOOL_ROUNDS = 5`. After you merge it, the live test passes and the version is approved.

Both branches start from the latest `main`. Each one goes back into `main` through its own pull request.

## Step 1: Start from a clean, passing main

```bash
cd ~/hr-rag-lab
git switch main
git pull --ff-only
git status --short
grep -n '^MAX_TOOL_ROUNDS' lambda/app/assistant.py
```

**Expected:** `git status --short` prints nothing, and the last line is `54:MAX_TOOL_ROUNDS = 5`.

Before you break anything, write down three things from your last passing run:

- the commit,
- the prompt version,
- the Lambda version that the `approved` alias points to.

An **alias** is a name that points to one version of the Lambda function. This command prints the version behind `approved`:

```bash
aws lambda get-alias \
  --function-name "$(terraform -chdir=infra/terraform output -raw candidate_function)" \
  --name approved \
  --query FunctionVersion --output text
```

## Step 2: Break it

Create the branch and find the line:

```bash
git switch -c test/tool-limit
grep -n '^MAX_TOOL_ROUNDS' lambda/app/assistant.py
```

**Expected:** `54:MAX_TOOL_ROUNDS = 5`. The number before the colon is the line number.

Make the change in VS Code:

1. Open `lambda/app/assistant.py`.
2. Press **Ctrl+G**, type the line number from `grep`, and press **Enter**. The cursor jumps to that line.
3. Change the line to `MAX_TOOL_ROUNDS = 1`.
4. Save the file with **Ctrl+S** (**Cmd+S** on a Mac).

Check the change before you commit:

```bash
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
2. Watch the `checks` job. **It passes**, because the code itself is still valid.
3. Get reviewer approval and merge.

You merge a broken change on purpose here. It is a planned test in staging, with made-up data.

## Step 4: Watch the gate block the release

The **release gate** is the point in the pipeline where a failed test stops a version from being approved.

In GitHub, open the **Actions** tab. Click the **new** run on `main`.

**Expected:**

- `Test the real authenticated application` fails.
- Promptfoo shows failed assertions.
- `Approve the exact tested staging version` is **skipped**.
- The report says `Release gate: FAIL.`.
- `Production handoff (dry run)` is **skipped**.

The pull request is already merged. What the gate blocked is the **release**: the broken version is never approved.

Check that the `approved` alias did not move:

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

The staging app always runs the newest version, through the `candidate` alias. So it shows the broken answer, even though the release is blocked.

In Langfuse, open the trace for that question. You see **Agent round 1** with its policy search, and no **Agent round 2**. The limit stopped the assistant before it could write the answer. On the **HR answer** step, the metadata says `stopped: tool round limit reached (1)`. Its output is the "couldn't finish" message.

You can see the same thing in the model gateway, which records every call the app makes to the AI model:

1. Open the gateway admin page, as you did in document 03, step 3.
2. Click **Logs**.
3. Find this question. Compare its model calls with the same question from your passing run. The broken version makes fewer calls.

## Step 6: Repair it with a new branch

The broken change is already in `main`. So the repair needs its own branch and its own pull request.

```bash
git switch main
git pull --ff-only
git switch -c fix/tool-limit
grep -n '^MAX_TOOL_ROUNDS' lambda/app/assistant.py
```

In VS Code:

1. Open `lambda/app/assistant.py`.
2. Press **Ctrl+G** and go to the line `grep` printed.
3. Change it back to `MAX_TOOL_ROUNDS = 5`.
4. Save the file.

Then check it:

```bash
git diff
```

**Expected:** one changed line, from `1` back to `5`.

```bash
git add lambda/app/assistant.py
git commit -m "Restore the working tool budget"
git push -u origin fix/tool-limit
```

Open a pull request from `fix/tool-limit` into `main`, get it reviewed, and merge it.

## Step 7: Confirm the repair

In GitHub, open the **newest** run on `main`.

**Expected:** every job is green, the report says `Release gate: PASS.`, and the `approved` alias now points to the new version:

```bash
aws lambda get-alias \
  --function-name "$(terraform -chdir=infra/terraform output -raw candidate_function)" \
  --name approved \
  --query FunctionVersion --output text
```

Ask the same PTO question again. In Langfuse, the new trace shows **Agent round 1** with the policy search. Then it shows **Agent round 2** with the answer, the inline judge and the answer guardrail. The **inline judge** is a second model call that checks the answer against the policy text before the employee sees it.

If a different case fails, open its trace in Langfuse to see why.

## Step 8: Clean up the branches

```bash
git switch main
git pull --ff-only
git branch -D test/tool-limit fix/tool-limit
```

## Evidence to keep

- The bad commit and the fix commit.
- The link to the failing run and the link to the passing run.
- The two Langfuse trace links for the PTO question, before and after.
- The `approved` version before, during and after.

**Next:** [07b Use case 2: wrong prompt instruction](07b-use-case-2-wrong-prompt-instruction.md)
