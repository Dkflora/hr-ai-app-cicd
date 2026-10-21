"""The guardrail wrapper, with a stand-in for the Bedrock client (no AWS needed)."""

from app import config, guardrails


class FakeBedrock:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def apply_guardrail(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


def use_fake(monkeypatch, response):
    fake = FakeBedrock(response)
    monkeypatch.setattr(config, "GUARDRAIL_ID", "gr-123")
    monkeypatch.setattr(config, "GUARDRAIL_VERSION", "1")
    monkeypatch.setattr(guardrails, "bedrock", lambda: fake)
    return fake


def test_skipped_when_no_guardrail_is_configured(monkeypatch):
    monkeypatch.setattr(config, "GUARDRAIL_ID", "")
    assert guardrails.check("anything", "INPUT") == ("allowed", "anything")


def test_passes_text_through_when_the_guardrail_allows_it(monkeypatch):
    fake = use_fake(monkeypatch, {"action": "NONE", "outputs": []})
    assert guardrails.check("How many sick days?", "INPUT") == ("allowed", "How many sick days?")
    assert fake.calls[0]["source"] == "INPUT"
    assert fake.calls[0]["content"] == [{"text": {"text": "How many sick days?"}}]


def test_returns_the_refusal_when_a_policy_blocks(monkeypatch):
    use_fake(monkeypatch, {
        "action": "GUARDRAIL_INTERVENED",
        "outputs": [{"text": "Blocked."}],
        "assessments": [{"sensitiveInformationPolicy": {"piiEntities": [
            {"type": "US_SOCIAL_SECURITY_NUMBER", "action": "BLOCKED"}]}}],
    })
    assert guardrails.check("My SSN is 536-22-1234", "INPUT") == ("blocked", "Blocked.")


def test_returns_the_masked_text_when_contact_details_are_anonymized(monkeypatch):
    use_fake(monkeypatch, {
        "action": "GUARDRAIL_INTERVENED",
        "outputs": [{"text": "Call me on {PHONE} about PTO"}],
        "assessments": [{"sensitiveInformationPolicy": {"piiEntities": [
            {"type": "PHONE", "action": "ANONYMIZED"}]}}],
    })
    assert guardrails.check("Call me on 555-201-3344 about PTO", "INPUT") == ("masked", "Call me on {PHONE} about PTO")
