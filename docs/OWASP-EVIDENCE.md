# OWASP LLM risk coverage across the HR and Kubernetes projects

This mapping uses the OWASP LLM Top 10 **2025 edition**, the reference used to design these projects. Consult [OWASP’s official publication and release history](https://genai.owasp.org/llm-top-10/) when updating the threat model. This document does not claim to use the latest edition.

The two projects address all ten risk categories through controls, exercises and evidence review. Coverage of a category does not mean every attack is prevented. A trace makes behavior observable; it does not enforce authorization or make an answer correct.

## Combined coverage map

| Risk | Kubernetes troubleshooting project | HR policy project | Evidence and remaining work |
|---|---|---|---|
| LLM01 Prompt injection | Inspect whether untrusted logs or tool output redirect the assistant; keep tool permissions outside the model. | Guardrails, restricted tools and retrieval access checks; adversarial cases 15–17 and 40. | Preserve the attempted redirection, authorized tool behavior and safe result. Kubernetes log-injection exercise must be verified; passing HR cases do not prove every injection is blocked. |
| LLM02 Sensitive information disclosure | Restricted read-only kubeconfig for synthetic workloads; masking and trace-content review. Read access can still expose logs and sensitive objects. | Cognito, database row-level security, retrieval filtering and cross-user tests. | Show rejected access, absent restricted facts and redacted telemetry. Verify masking in the Kubernetes deployment; shared classroom identity does not demonstrate individual user isolation. |
| LLM03 Supply chain | Review and pin the agent, MCP dependencies and self-hosted Langfuse images. | Review dependencies, lockfiles, GitHub Actions and gateway image versions. | Record dependency/image provenance and update ownership. Complete integrity and vulnerability review is still required; installing an evaluation tool does not address this risk. |
| LLM04 Data and model poisoning | Treat cluster logs and tool results as untrusted evidence; review unexpected changes before drawing conclusions. | Approved policy manifest, labels, versions and validation before ingestion/index rebuild. | Demonstrate rejection of an unapproved or malformed policy fixture. Log injection is related but does not replace a poisoning test. Neither project trains a model; external model provenance remains a dependency. |
| LLM05 Improper output handling | Keep suggested commands as text; never execute model-generated shell commands automatically. Enforce read-only tools. | React text rendering, parameterized database operations and validated tool arguments. | Test unsafe output rendering and rejected invalid arguments. Review every downstream consumer; read-only RBAC alone does not prevent unsafe HTML rendering. |
| LLM06 Excessive agency | Read-only RBAC, restricted tools and bounded tool loop; trace a limit failure, repair it and rerun. | Two bounded read tools, backend authorization and finite loop. | Show denied writes/unknown tools and enforcement independent of the judge. Do not enable pod deletion on the shared cluster. |
| LLM07 System prompt leakage | Keep credentials out of prompts and tool-visible results; inspect attempted instruction disclosure. | Prompt contains no credentials; credentials remain in Secrets Manager. | Add/verify a prompt-extraction attempt and inspect the result. A refusal is defense in depth; prompt secrecy must not be an authorization boundary. |
| LLM08 Vector and embedding weaknesses | Not applicable to the troubleshooting baseline unless it adds vector retrieval. | Retrieval access labels, country/version filtering and approved policy ingestion. | Restricted-document and stale-policy cases, including historical/current policy comparisons. Review extraction/chunking fixtures and index provenance. |
| LLM09 Misinformation | Compare answers against actual tool results; Langfuse grounding judge and trace → fix → rerun exercise. | Reference facts, citations, inline judge, bounded revision and safe fallback. | Compare automated scores with human/domain review. The current gateway-backed HR run still has two failing required cases; judge scores do not establish calibrated confidence. |
| LLM10 Unbounded consumption | Finite tool rounds, model token bounds, timeouts and cost/latency tracing. | LiteLLM key budgets, request/token limits, model restrictions and bounded retries. | Gateway allowed/denied-call tests and application traces. Kubernetes has loop bounds, not a proven centralized spend cap. HR embeddings, Guardrails and infrastructure need separate cost monitoring; per-employee budgets and alerts remain gaps. |

## How to record verification

For each exercise record the source/configuration version, input scenario, expected result, actual result, trace or test report, and any repair followed by a rerun. Mark evidence **passed**, **failed**, **not yet verified**, or **not applicable with justification**.

Kubernetes entries above describe the agreed controls and exercises. This document is not evidence of a fresh Kubernetes rehearsal. Verify those entries against its repository and actual traces before marking them passed.

For HR, use the [change, test and evidence map](CHANGE-TEST-EVIDENCE-MAP.md), [failure exercises](FAILURE-EXERCISES.md), and [gateway configuration](LLM-GATEWAY.md). A passing local test is distinct from a passing authenticated application test and a complete hosted release run.

## Scope boundaries

All ten categories have an assigned treatment across the two projects. Supply-chain review, poisoning fixtures, prompt-extraction checks and Kubernetes masking need explicit evidence before they can be described as verified. Production availability, isolated production promotion and automatic rollback require additional implementation. This coverage map is a threat-model and evidence checklist, not a security certification.
