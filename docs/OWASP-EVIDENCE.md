# OWASP LLM risk review: evidence, not certification

| Risk | Existing or planned mitigation | Evidence to collect / remaining gap |
|---|---|---|
| LLM01 Prompt injection | Guardrails, untrusted retrieved text, limited tool definitions | Malicious question and document cases; safe output and no unauthorized lookup |
| LLM02 Sensitive information disclosure | Cognito, database RLS, retrieval access filtering, tracing content off by default | Cross-user and cross-role negative tests; no credentials in traces or PR reports |
| LLM03 Supply chain | Reviewed dependencies, lockfiles and pinned GitHub Actions | Dependency provenance and review evidence; action/dependency pins require maintenance; comprehensive supply-chain auditing remains a gap |
| LLM04 Data/model poisoning | Approved manifest, labels, versions, validation before index rebuild | Reject malformed/unapproved files; source provenance and review remain necessary |
| LLM05 Improper output handling | React text rendering, parameterized database operations, strict tool arguments | Test unsafe HTML/script strings and invalid arguments; inspect all downstream consumers |
| LLM06 Excessive agency | Two bounded read tools, backend authorization, finite loop | Reject unknown tools and prohibited requests; judge does not grant permission |
| LLM07 System prompt leakage | Prompt contains instructions rather than credentials | Attempts to extract prompt; secrets must stay in Secrets Manager, not the prompt |
| LLM08 Vector/embedding weaknesses | Access labels enforced in retrieval; version/country filtering | Restricted-document cases, stale-version cases, ingestion/extraction fixtures |
| LLM09 Misinformation | Source citations, reference facts, inline judge and fallback | Supported/unsupported answer tests; judge calibration against domain-reviewed labels |
| LLM10 Unbounded consumption | LiteLLM application-key budgets and RPM/TPM limits, loop/token bounds, Lambda/API timeouts | Gateway denial, throttling, retry and outage tests; embeddings/Guardrails/infrastructure need separate cost monitoring; employee-specific budgets and budget alerts remain gaps |

OWASP is an industry risk reference. This table is a teaching mapping, not a security certificate. A risk is not closed merely because a tool is installed. Mark each result implemented and tested, failed, not yet tested, or not applicable with justification. Keep known gaps visible.
