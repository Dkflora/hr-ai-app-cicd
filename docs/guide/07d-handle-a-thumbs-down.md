# 07d Handle a thumbs down

**Goal:** follow one thumbs down from the moment someone clicks it to the moment the team decides what to fix. On the way, you set up an email alert for thumbs down.

## Tests before a release, signals after

The 52 test cases are the **golden set**: fixed questions with known correct answers. The pipeline runs them before every release. They catch the mistakes you already know about.

Real people then ask questions nobody wrote a test for. Their **thumbs down** is how you find the new mistakes. Under each answer, the app shows 👍 and 👎. A vote is saved in Langfuse as a score named `user_feedback` on that answer's trace: `true` for 👍, `false` for 👎. An optional comment is saved with it, with personal data masked.

A thumbs down on its own changes nothing. A company decides who looks at it, how fast, and what happens next. This document walks through that process:

1. **Alert:** someone is told that a thumbs down arrived.
2. **Collect:** the answer goes into a review queue.
3. **Review:** an expert reads the trace and records why the answer went wrong.
4. **Fix and protect:** the fix ships through the pipeline, and the question joins the golden set.

## Step 1: Turn on the email alert

Setup created an alarm in Amazon CloudWatch, `hr-ci-ai-chatbot-thumbs-down`. It works like this:

- When someone votes, the chat function writes the score to its log.
- A **metric filter** counts every log line that holds a thumbs down.
- The **alarm** goes off when that count is above 0 in a 5-minute window. It sends a message to the project's alarm topic in Amazon SNS (Simple Notification Service), which emails everyone subscribed.

Subscribe your email address to the topic. Replace `you@example.com` with your own address:

```bash
cd ~/hr-rag-lab
aws sns subscribe --protocol email --notification-endpoint you@example.com --topic-arn "$(terraform -chdir=infra/terraform output -raw alarm_topic_arn)"
```

**Expected:** the command prints `"SubscriptionArn": "pending confirmation"`. Within a few minutes, you get an email titled **AWS Notification - Subscription Confirmation**. Click **Confirm subscription** in it.

The same topic also receives the project's other alarms: chat errors, server errors and slow answers.

## Step 2: Give a thumbs down

1. Open the staging app and sign in as Amara.
2. Ask: `Can I bring my dog to the office?`
3. Under the answer, click 👎.
4. In the box that appears, type `Practice: testing the review process`, and click **Send**.

**Expected:** the app shows `Thanks for the feedback.`

## Step 3: Get the alert

Within about 5 minutes, you get an email titled **ALARM: "hr-ci-ai-chatbot-thumbs-down"**. It names the alarm and its description: *Someone marked an answer as not helpful.*

You can also see the alarm in the AWS console. Open **CloudWatch**, then **Alarms**. `hr-ci-ai-chatbot-thumbs-down` shows **In alarm**. After 5 minutes with no new thumbs down, it goes back to **OK** on its own.

An alarm emails only when it changes to **In alarm**. More thumbs down while it is already in alarm send no new email.

## Step 4: Queue the answer for review

```bash
python scripts/review-thumbs-down.py
```

The script finds every thumbs down from the last 7 days and adds each answer's trace to a Langfuse **annotation queue**: a list of answers waiting for a reviewer. On its first run it also creates:

- The queue, **Thumbs-down review**.
- A score called `failure_cause`, with the five causes a reviewer can pick from (see step 5).

Running the script again is safe. It never adds the same answer twice.

**Expected:**

```text
Thumbs down in the last 7 days: 1. Newly queued: 1.
In Langfuse, open the "Thumbs-down review" annotation queue to review them.
```

The first run also prints `Created score config failure_cause` and `Created annotation queue "Thumbs-down review"`.

## Step 5: Review it in Langfuse

In Langfuse, open **Annotation Queues**, then **Thumbs-down review**. Your answer is the first item. Read its trace from top to bottom:

1. The **question**, and the comment from the 👎.
2. The **policy search**: which passages came back?
3. The **model's answer**: does it match those passages?
4. The **inline judge**: did it accept or reject the draft?

Then pick the `failure_cause` that fits, and click to complete the item:

- `retrieval`: the search missed the passage that answers the question. The fix is in the documents or the search.
- `prompt`: an instruction in the prompt steered the answer wrong. The fix is a new prompt version.
- `model`: the right passage came back, but the answer misread it. The fix is in the prompt or the inline judge.
- `policy_gap`: no document answers the question. The fix goes to the HR team, not the code.
- `not_wrong`: the answer was correct, and the person disliked it, for example because the answer was "no".

No policy mentions dogs, so the app answers `I could not verify that answer. Please contact People Operations.` That makes it `policy_gap`, or `not_wrong` if a refusal is the right answer. A thumbs down does not always mean the app made a mistake. That is why a person reviews it before anyone changes code.

## Step 6: Fix and protect

When the cause is `retrieval`, `prompt` or `model`, the fix goes through the pipeline. You know the steps from documents 07a to 07c: a branch, a pull request, a new `VERSION`, and a merge.

The same pull request adds the question to the golden set, in `lambda/data/evaluation_questions.json`. A test case looks like this:

```json
{
  "group": "everyday",
  "email": "qa.employee@northwind.example",
  "question": "How many unused vacation days can I carry over?",
  "must_include": ["5"],
  "source": "Time Off Policy"
}
```

From then on, every release must answer that question correctly. The same mistake cannot come back unnoticed.

You do not add a case in this lab. The rest of the guide counts on the 52 cases.

## How companies alert on feedback

The lab's alarm emails on every single thumbs down, so you can see it work. With real traffic, that would be too noisy. Companies usually change three things:

- **Alert on a rate, not a vote.** For example: more than 10% thumbs down in the last hour, with at least 20 votes. One unhappy person does not wake anyone up.
- **Send it where the team works.** A Slack or Teams channel, or the on-call tool, instead of one person's inbox.
- **Compare releases.** Each trace carries its release, such as `v1.0.4`. A thumbs-down rate that doubles after a release is a reason to roll back, as in document 08, even when every golden test passed.

Langfuse can do this too, with its own **Alerts**. An alert can watch a score such as `user_feedback`. Its average is the share of 👍, so you can alert when it drops below a value you choose, such as 0.8 over one day. Langfuse sends the alert to Slack, to a webhook, or to a GitHub Actions workflow. It cannot send email. The free Langfuse plan allows 2 alerts.

**Next:** [08 Production handoff and rollback](08-production-handoff-and-rollback.md)
