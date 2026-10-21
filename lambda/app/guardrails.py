"""Amazon Bedrock Guardrails: check the question before answering, and the answer before sending it.

The guardrail (created by Terraform in bedrock.tf) blocks harmful content and
prompt-injection attempts. For personal data it does one of two things:

  BLOCK      Social Security, card and bank account numbers. The whole text is replaced.
  ANONYMIZE  Email addresses and phone numbers. Only that part is replaced, for
             example with {EMAIL}, and the rest of the question is still answered.

We call it with the ApplyGuardrail API, separately from the model, so the same
checks work whatever model writes the answer.

Until the guardrail exists GUARDRAIL_ID is empty and the checks are skipped,
so the assistant still answers while you are part way through building the stack.
"""

from functools import cache

from app import config

# What is stored and traced in place of a blocked question, so the blocked value
# never reaches the chat history, the request log or Langfuse.
REMOVED = "[Removed: the message contained sensitive information]"


@cache
def bedrock():
    import boto3

    return boto3.client("bedrock-runtime", region_name=config.AWS_REGION)


def was_blocked(response):
    """True when any guardrail policy blocked the text, False when it only masked parts of it."""
    for assessment in response.get("assessments", []):
        # One entry per policy: content filters, sensitive information, and so on.
        for policy in assessment.values():
            if not isinstance(policy, dict):
                continue
            # Each policy lists its findings, for example piiEntities or filters.
            for findings in policy.values():
                if not isinstance(findings, list):
                    continue
                for finding in findings:
                    if isinstance(finding, dict) and finding.get("action") == "BLOCKED":
                        return True
    return False


def check(text, source):
    """Check one piece of text.

    source  "INPUT" for the employee's question, "OUTPUT" for the answer.

    Returns (status, text_to_use):
      "allowed"  nothing found; text_to_use is the original text
      "masked"   personal data was replaced, for example with {PHONE}; the rest is kept
      "blocked"  the text must not be used; text_to_use is the guardrail's refusal message
    """
    if not config.GUARDRAIL_ID:
        return "allowed", text

    response = bedrock().apply_guardrail(
        guardrailIdentifier=config.GUARDRAIL_ID,
        guardrailVersion=config.GUARDRAIL_VERSION,
        source=source,
        content=[{"text": {"text": text}}],
    )

    if response["action"] != "GUARDRAIL_INTERVENED":
        return "allowed", text

    replacement = " ".join(output["text"] for output in response.get("outputs", []))
    if was_blocked(response):
        return "blocked", replacement or "Sorry, I can't help with that request."
    return "masked", replacement or text
