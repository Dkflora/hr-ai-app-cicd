# What this HR lab costs

Costs depend on resource lifetime, active compute, model tokens, storage and requests. The table below separates fixed infrastructure charges from usage charges; it does not estimate a fixed daily total.

| Component | Current configuration and billing |
|---|---|
| Private interface endpoints | Three services (Bedrock, Secrets Manager and OpenSearch), each in two Availability Zones: six billed endpoint interfaces. At $0.01 per interface-hour, that is **$0.06/hour**, **$0.24 for four billed hours**, or **$1.44 for 24 hours**, before data processing. This is the network portion only, not the total lab bill. |
| OpenSearch | NextGen collection group with minimum indexing/search capacity zero. Compute scales to zero after inactivity; active OCUs and storage are charged. |
| Aurora | Serverless v2 minimum zero, with auto-pause after 15 idle minutes. Active compute, storage and I/O can still cost money; ongoing connections/traffic can prevent pausing. |
| LiteLLM gateway | One t3.medium instance, encrypted EBS storage and a public IPv4 address add ongoing charges. Its separate database uses the existing Aurora cluster; persistent proxy connections can prevent Aurora auto-pause. The configured $5 model allowance is not a daily infrastructure charge. |
| WAF | Standard web ACL base charge is $5 **per month**, plus rules and requests, not $5 per day. Resource lifetime affects prorated charges. |
| Model and evaluations | Bedrock generation, inline judging, DeepEval judging, embeddings and Guardrails add usage charges. Each full API comparison makes 86 application requests, plus associated model/tool calls; repeated runs increase usage. Langfuse/Promptfoo views replay captured outputs in this workflow. |
| Other services | Secrets Manager, logs, S3, API Gateway, Lambda, Cognito and CloudFront depend on storage, requests, transfer and account allowances. Do not assume every account has free-tier coverage. |

The endpoint subtotal assumes us-east-1 and the published $0.01 per interface-hour rate. Partial endpoint hours are billed as full hours. Count time from provisioning until deletion, including setup and teardown; a four-hour session does not necessarily mean four hours of billed infrastructure.

## Keep the exercise economical

- Use the provided one-Aurora-instance configuration.
- Keep the existing scale-to-zero settings; do not switch to Classic OpenSearch.
- Reuse captured outputs for offline assertion/experiment inspection rather than generating another answer unnecessarily.
- Run the chosen failure and repair exercises; extra full live runs add model usage.
- Destroy your lab when finished, using the documented teardown steps. Merely stopping questions does not stop private-endpoint charges.

Confirm actual costs in AWS Billing/Cost Explorer once usage appears. This document provides component estimates, not a measured total or spending cap.

Sources: [AWS PrivateLink pricing](https://aws.amazon.com/privatelink/pricing/), [OpenSearch NextGen pricing](https://aws.amazon.com/opensearch-service/pricing/), [AWS WAF pricing](https://aws.amazon.com/waf/pricing/), [Aurora auto-pause](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2-auto-pause.html).
