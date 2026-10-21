# 03 Sign in and read your first trace

**Goal:** use the chatbot as an employee and follow that one request through Langfuse and the model gateway.

This is the trace you will compare against when something breaks in the use cases.

## Step 1: Sign in and ask a question

The app address, the demo employees and their shared password are in `demo-sign-in.txt` in the project folder. Open it in your editor, or print it:

```bash
cd ~/hr-rag-lab
cat demo-sign-in.txt
```

Open the app address and sign in as `amara.diallo@northwind.example`, an employee who sees only her own record.

Ask:

> How many PTO days do employees receive each year?

Then ask a follow-up in the same conversation:

> How many of those can I carry over?

Under the second answer, click 👎 and type a short reason, such as `I wanted my own balance`, then click **Send**. Every answer has 👍 and 👎. A rating becomes a score on that answer's trace, so someone can review every answer people disliked.

## How Langfuse records a request

Langfuse uses four words:

- **Trace:** the record of one request, from question to answer.
- **Span:** one step inside a trace, such as a tool call or a model call, with its timing.
- **Session:** all the traces of one conversation.
- **Prompt version:** the numbered version of the system prompt that produced the answer.

One of those spans is the **inline judge**. Before the employee sees an answer, a second model call checks the draft against the evidence the tools returned. A failing draft gets one revision. If that also fails, the employee gets a safe fallback answer instead. The judge is always on.

## Step 2: Find the trace in Langfuse

Langfuse shows what the application did with each question.

In Langfuse, open your project and go to **Sessions**. Open the newest session. You should see:

- An opaque user ID (the trace never shows the employee's email), and the tags `employee` and `person`.
- Both questions in the same session.
- The **prompt version number** used for the answer.

Open one trace. Its steps form a tree, in the order they ran:

- **HR answer**: the question, the answer and its sources. Its metadata sums up the request: outcome, rounds used, tools used, tokens, and what each guardrail decided.
  - **Agent round 1**: the model's first turn.
    - **Bedrock model call**: everything sent to the model (the system prompt and the messages), its reply, the settings, the tokens and the cost. Here the reply is a request to search the policies, with the search text the model wrote.
    - **Authorized HR tool**: the arguments the model wrote, and the text sent back to it.
      - **Policy search**: the access levels this role gets, the filters, which searches ran, and each passage with its similarity score.
        - **Titan embedding** and **OpenSearch vector query**: the search itself, each with its timing.
  - **Agent round 2**: the model writes the answer from the passages.
    - **Bedrock model call**: the draft answer.
    - **Inline judge**: the outcome, such as `passed first time`. Under it, **Inline grounding assessment** shows the verdict and the reason.
    - **Bedrock Guardrail: answer**: whether the answer was allowed, masked or blocked, and what kind of data it found.

Click any step to see its input, output and metadata. Langfuse highlights a step with a warning, such as a judge that rejected a draft.

Open the trace of the second answer. Under **Scores** it shows `user_feedback` with the value `false` and your reason. Personal data in a reason, such as a phone number, is masked before it is stored. To review every unhelpful answer, go to **Scores** or **Traces** and filter on `user_feedback`. A team can also send those traces to an **annotation queue**, where an HR expert grades them.

## Step 3: See the same questions in the model gateway

Every model call from the app goes through the LiteLLM gateway. Its admin UI shows each call with its model, cost and cache result. Langfuse shows the application's view of a request, and the gateway shows the model calls it made.

The gateway accepts connections only from the application Lambda. You reach its UI through an AWS Systems Manager (SSM) tunnel, which forwards the gateway's port 4000 to your computer. Your AWS permissions decide who can open it.

1. Install the [Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html) once.
2. Open a **second** terminal. The tunnel keeps it busy until you close it.
3. In that terminal, go to the project and activate the virtual environment you created in document 02. Every new terminal needs this before running the lab's Python scripts.

```bash
cd ~/hr-rag-lab
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate
python scripts/open-gateway-ui.py
```

The script prints the address, `http://localhost:4000/ui`, and the sign-in. Open the address, then sign in as `admin` with the printed password. The same details are in `demo-sign-in.txt`. If port 4000 is busy on your computer, add `--port 4100` and use that port in the address.

The password is the gateway master key. It can create keys and change every limit, so keep it out of screenshots, tickets and chat.

Open **Logs** and find the two questions from step 1. Each question shows more than one model call: the answer and the inline judge.

When you are done, press Ctrl+C in the second terminal to close the tunnel.

## Step 4: See where the accounts live

The setup created two kinds of account in Cognito, each with its own password:

- **Demo employees:** Amara, Liam, Priya and Dana. These are the people who use the app; you just signed in as one.
- **Test accounts:** `qa.employee`, `qa.manager`, `qa.hr` and `qa.exec`. Only the pipeline and automated tests sign in as these.

In the AWS console, open **Cognito → User pools** and select the pool named after your `project_name`, ending in `-users`. Its **Users** tab lists both kinds of account.

How your sign-in protected the data in step 1:

1. The browser got a token from Cognito.
2. API Gateway checked the token before the Lambda ran.
3. The Lambda read the employee's email from the verified token, never from the request body.
4. Every database and search call was limited to what that employee may see.

## Step 5: How the pipeline signs in

The pipeline cannot click a sign-in page. The helper `ci/auth.py` signs in for it:

1. It reads the test accounts' password from their own secret in Secrets Manager.
2. It signs in through Cognito and keeps the tokens in memory only.
3. It calls the API through API Gateway, so the same data permissions apply.

The pipeline's AWS role can read only the test accounts' secret, never the demo employees' password.

After each run, the pipeline deletes the test accounts' chats. Your chats as a demo employee are never touched. To empty every account's history yourself, run `python scripts/clear-chat-history.py`.

You should now see your two questions in one Langfuse session, with each agent round, the policy search and the inline judge. Their model calls also appear in the gateway logs.

**Next:** [04 Branch and pull-request checks](04-branch-and-pr-checks.md)
