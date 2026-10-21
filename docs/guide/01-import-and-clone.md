# 01 Import and clone

**Goal:** get a working copy of the company's repository on GitHub and on your workstation.

In a company, the repository and the app belong to the team. For this lab, you import the repository into your GitHub account, so you can set up its pipeline the way the team's platform engineer would.

A plain clone of the source repository would not give you its Actions settings, environments and secrets.

## Step 1: Import the repository into your GitHub account

1. Open [GitHub Import](https://github.com/new/import).
2. Source URL: `https://github.com/kserge2001/hr-rag-cicd-student-starter.git`
3. Owner: **your own account**. Repository name: `hr-rag-lab`.
4. Visibility: **Public**. The data is synthetic, and private repositories need a paid GitHub plan for environment secrets.
5. Begin the import. The new repository's address must start with `https://github.com/YOUR-USERNAME/`.

If the importer refuses the source, open the source repository page and use **Use this template → Create a new repository** instead, with the same owner and name.

Then open your repository's **Settings → Actions → General** and make sure Actions are allowed.

## Step 2: Clone your copy and create the feature branch

```bash
cd ~
git clone https://github.com/YOUR-USERNAME/hr-rag-lab.git
cd ~/hr-rag-lab
git remote -v
git switch -c feature/pipeline
```

`origin` must point to **your** repository. You stay on `feature/pipeline` until document 06b.

## Step 3: Look around

These are the folders you will use:

```bash
ls frontend lambda/app infra/terraform ci
cat lambda/app/prompts/hr_system.txt
```

- `frontend/`: The React chat application.
- `lambda/app/`: The Python backend: chat handler, retrieval, tools, inline judge.
- `lambda/app/prompts/hr_system.txt`: The system prompt; it gets a version number in Langfuse on every release.
- `infra/terraform/`: All AWS infrastructure.
- `ci/`: Prepared pipeline helpers: packaging, deployment, API tests, evaluation adapters.

You configure and connect the `ci/` helpers in this lab. You do not write them.

**Next:** [02 Infrastructure setup](02-infrastructure-setup.md)
