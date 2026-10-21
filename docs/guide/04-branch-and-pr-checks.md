# 04 Branch and pull-request checks

**Goal:** create the first job of the delivery workflow and see it run on a pull request.

This job runs on every push and pull request. It runs the unit tests, builds the backend package with its release identity, and builds the React site. It gets **no AWS or Langfuse credentials**, because pull-request code has not been reviewed yet.

## What a CI workflow is

**CI** (continuous integration) means every change is checked automatically before it is merged. In GitHub Actions, a **workflow** is a YAML file in `.github/workflows/`. It has:

- **Triggers** (`on:`): the events that start it, such as a push or a pull request.
- **Jobs:** groups of work. Each job runs on a fresh machine called a **runner**, and jobs can wait for each other.
- **Steps:** the commands inside a job, run in order. A step either runs a shell command (`run:`) or a ready-made **action** (`uses:`), such as one that downloads your code.

If you know Jenkins or Azure DevOps: jobs are like stages, runners are like agents, and actions are like plugins or tasks. The comment at the end of each line in step 2 says what that line does.

This job also builds the backend package with its **release identity**: a `release.json` file inside the package that records the commit and a fingerprint of the prompt. Later, every test result can be traced back to the exact code and prompt it tested.

## Step 1: Run the unit tests locally

Run the same tests the job will run:

```bash
cd ~/hr-rag-lab
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate
python -m unittest discover -s ci/tests -v
```

**Expected:** every test ends with `ok`, and the last line is `OK`.

The tests check prompt structure, release packaging, the inline judge, the model gateway adapter and trace handling. See `ci/tests/test_release.py` for an example.

## Step 2: Create the workflow file

This command creates `.github/workflows/hr-quality.yml` with the complete first version.

```bash
mkdir -p .github/workflows
cat > .github/workflows/hr-quality.yml <<'EOF'
# Reviewed changes, staging evaluation and release approval.
name: HR application delivery and evaluation                            # pipeline name
on:                                                                     # trigger
  pull_request:                                                         # on pull request
  push:                                                                 # on push
    branches: [main, 'feature/**', 'fix/**', 'test/**']                 # branch filter
  workflow_dispatch:                                                    # manual run button
permissions:                                                            # token rights
  contents: read                                                        # read-only code
concurrency:                                                            # one run at a time
  group: hr-staging                                                     # queue name
  cancel-in-progress: false                                             # never cancel
jobs:                                                                   # stages
  # Validate proposed changes before giving code deployment credentials.
  checks:                                                               # job
    runs-on: ubuntu-24.04                                               # agent (pinned image)
    steps:                                                              # steps
      - uses: actions/checkout@v7                                       # get code
        with:                                                           # inputs
          persist-credentials: false                                    # drop Git token
      - uses: actions/setup-python@v7                                   # install Python
        with:
          python-version: '3.12'                                        # version
      - name: Install delivery helper dependencies                      # step title
        run: python -m pip install -r ci/requirements.txt               # install packages
      - name: Prompt structure and release contract tests
        run: python -m unittest discover -s ci/tests -v                 # unit tests
      - name: Build backend candidate with release identity
        run: python ci/release.py                                       # build package
      - uses: actions/setup-node@v7                                     # install Node.js
        with:
          node-version: '22'
          cache: npm                                                    # package cache
          cache-dependency-path: frontend/package-lock.json             # cache key
      - run: npm --prefix frontend ci                                   # install UI packages
      - run: npm --prefix frontend run build                            # build UI
EOF
```

What each part does:

- `on:`: Runs on pull requests, on pushes to `main`, `feature/**`, `fix/**` and `test/**`, and on a manual click.
- `permissions: contents: read`: The job can read the code and nothing else.
- `concurrency: hr-staging`: One run at a time, so two deployments never overlap in the single staging environment.
- `persist-credentials: false`: The Git token is not left on the runner after checkout.
- `ci/release.py`: Checks the prompt and packages the backend with a `release.json` that records the commit and prompt.

## Step 3: Commit and push

```bash
git add .github/workflows/hr-quality.yml
git commit -m "Add HR branch and pull-request checks"
git push -u origin feature/pipeline
```

## Step 4: Open the pull request

Open your repository on GitHub. Right after a push, a yellow banner above the file list shows `feature/pipeline` with a **Compare & pull request** button. Click it, then click **Create pull request**.

If the banner is gone, open the **Pull requests** tab and click **New pull request**. Set **base** to `main` and **compare** to `feature/pipeline`, then click **Create pull request**.

The pull request page lists the `checks` job near the bottom. Click **Details** to follow its log.

**Expected:** the `checks` job finishes green.

**Do not merge yet.** Documents 06a and 06a2 add the deployment jobs to this same pull request.

**Next:** [05 GitHub-to-AWS access](05-github-to-aws-access.md)
