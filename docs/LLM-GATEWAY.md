# LLM gateway and consumption controls

## Request path

The HR backend translates Bedrock-shaped messages and tools to LiteLLM’s standard chat-completions route. LiteLLM resolves the approved model and calls Bedrock using its own scoped IAM role. Generation, model fallback, inline judging and the single revision use the same application virtual key. The CI DeepEval judge invokes the private evaluation Lambda, which uses that same gateway path. The browser and GitHub runner never receive the gateway key.

Aurora hosts a separate `litellm` database owned by `llm_gateway`. Its key, budget and usage tables are separate from the HR database. The HR app role cannot administer LiteLLM, and the gateway role cannot connect to the HR database. The setup Lambda creates this database, then the proxy performs its own version-specific migrations.

## Provisioning

Terraform provisions a dedicated gateway instance, security groups and Secrets Manager entries. The instance installs the pinned LiteLLM container and reaches the existing private Aurora cluster. It has outbound internet connectivity for image installation and management, but no public inbound application or SSH rule. Only the application Lambda security group can reach the gateway port. SSM is the administrative path.

The current single-instance synthetic deployment uses private VPC HTTP for Lambda-to-gateway traffic. This is not a high-availability production gateway. Production requires TLS on that hop, controlled image distribution, monitoring, recovery, capacity planning and an independently reviewed deployment architecture.

Setup creates a scoped key automatically and waits for initialization. No manual key copying is needed. Credentials remain in Secrets Manager and protected Terraform state; do not share state, plans or bootstrap environment files.

## Implemented controls

| Control | Enforcement |
|---|---|
| Approved models | Scoped virtual key plus gateway IAM and application allowlist |
| Request rate | Application key configured for 120 requests per minute |
| Token rate | Application key configured for 120000 tokens per minute |
| Concurrent requests | Application key configured for two parallel requests |
| Model spend | Application key budget of $5 per 24-hour window; this is an allowance, not a daily charge or complete AWS cost cap |
| Output tokens | Application adapter rejects limits above 2048; existing application generation bounds still apply |
| Retry amplification | No proxy retries; application model fallback retains the same key; budget, authorization and rate denials do not trigger fallback |
| Judge bypass | Inline judge/revision and CI judge use the gateway rather than direct model IAM access |

Spend enforcement uses recorded usage. Accounting delays and in-flight requests can cause overshoot; do not treat the budget as an exact prepaid ceiling. PostgreSQL must remain connected. Application model calls fail if the gateway is unavailable; there is no direct-provider escape path.

This allowance covers generation and judges. Titan embeddings and Bedrock Guardrail checks remain direct AWS calls with scoped IAM and are not charged to this LiteLLM key. Overall cost monitoring must include those services and infrastructure too. The application uses a shared service key: this implementation has an application-level budget, not a separate employee budget. Langfuse still groups application traces by user and session.

## Changes and evidence

- `infra/terraform/gateway.tf`: service, IAM, secrets, networking and instance.
- `gateway-bootstrap.sh.tftpl`: proxy configuration, database connection and scoped key initialization.
- `lambda/app/setup_db_handler.py`: isolated database/user setup.
- `lambda/app/model_gateway.py`: native request adapter and fail-closed errors.
- `scripts/initialize-gateway.py`: automatic initialization wait within setup.
- `ci/tests/test_gateway.py`: request preservation, denied limits, allowed models and missing configuration.

Verify an allowed request, unknown model, exhausted budget, token/request throttling, judge use and an unavailable gateway. Denied requests must not fall back directly to Bedrock. Collect proxy status, usage records, application trace and the passing/failing workflow evidence. Do not print keys or raw secret-bearing proxy errors.

Sources: [LiteLLM Bedrock passthrough](https://docs.litellm.ai/docs/pass_through/bedrock), [budgets and database requirement](https://docs.litellm.ai/docs/proxy/users), [virtual keys](https://docs.litellm.ai/docs/proxy/virtual_keys).
