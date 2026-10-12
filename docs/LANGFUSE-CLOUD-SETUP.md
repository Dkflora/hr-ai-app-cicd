# Langfuse Cloud setup for the HR lab

This lab uses Langfuse Cloud. The Kubernetes lab demonstrates Docker Compose self-hosting instead.

1. Open [Langfuse Cloud](https://cloud.langfuse.com). Choose GitHub or Google sign-in where offered. Complete account verification if requested.
2. Create or join the organization for your lab work. Create a separate HR lab project so its data and keys are distinct from other projects.
3. Confirm the selected cloud region and the exact API base URL shown for that project. Keep evaluation data within the environment approved for the lab. Do not guess the endpoint from another project.
4. Open the project's settings and API key section. Generate the public and secret keys for the lab. The secret key is sensitive even though the public key is not.
5. Configure LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY as GitHub Actions environment secrets in hr-staging. Configure LANGFUSE_BASE_URL as an environment variable using the project endpoint. Restrict deployments and secret access to reviewed branches.
6. For local testing, load the keys through a local ignored environment file or a secret manager. Never commit them, place them in the React build, display them in shared screenshots, or paste them into a PR report.
7. Run the connection check from the pipeline environment. Verify a candidate prompt version and a synthetic dataset experiment appear in the correct project.
8. Verify trace export separately. The HR Lambdas are in private subnets without internet egress in the original architecture. They require an approved export path to reach Langfuse Cloud; account setup alone does not establish that path.

Information required: project name, organization, cloud region, API endpoint, public key, secret key, and the approved synthetic dataset. If using a Langfuse-hosted model judge, its provider connection is an additional configuration; it is not required to repeat the Kubernetes judge setup in this lab.

See [Langfuse tracing setup](https://langfuse.com/docs/observability/get-started) and [GitHub AWS OIDC](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws) for the corresponding configuration patterns.

For local setup, open the ignored `.env.langfuse` in Notepad and save with Ctrl+S. Public keys begin `pk-lf-`; secret keys begin `sk-lf-`. Double quotes are optional. Use the exact region endpoint: a US project uses `https://us.cloud.langfuse.com`. Verify authentication before troubleshooting instrumentation. A connection smoke test is not an application trace.
