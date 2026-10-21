# 08 Production handoff and rollback

**Goal:** understand where staging approval ends, and practise putting the `approved` pointer back on an earlier version.

## What the production job does

The `production-handoff-dry-run` job runs only after the `candidate` job succeeds. It downloads the evidence the candidate job uploaded and checks two things:

1. `release.json` records the same commit that was merged.
2. The report contains `Release gate: PASS.`

Then it prints what production would receive. It changes no resources and moves no traffic. Open its log in your last passing run and read the three printed lines.

## From staging to production

- **Validate**. This lab: deploy and test the candidate in staging. Production: the same checks against the intended release.
- **Approve**. This lab: the `hr-production-approval` environment. Production: an authorized release reviewer.
- **Deploy**. This lab: dry run only. Production: the tested backend package, React build and exact prompt version, with a separate production role and configuration.
- **Verify and recover**. This lab: keep staging results and the `approved` pointer. Production: smoke-test production, monitor errors and quality, restore the last approved release if needed.

To make the job real, replace its dry-run step with production deployment and verification steps. Production must use the tested artifact, never a fresh rebuild.

## Two Lambda aliases

- `candidate`, moved by `ci/deploy_candidate.py`, on every merge: The version under test. The staging UI and API use it.
- `approved`, moved by `ci/promote_lab.py`, only after every required check passes: The last version that passed. Production would deploy this one.

When `promote_lab.py` moves `approved`, it writes the version it replaced into the alias description, such as `previous approved version: 7`.

## Rollback: restore the previous approved version

`ci/rollback_lab.py` reads that recorded version from AWS and moves `approved` back to it. It refuses a version outside the staging function, and it never deletes anything.

This step is optional. It needs at least two passing runs, so that `approved` has an earlier version to go back to. The fix run from use case 1 is one.

### Step 1: Roll back

```bash
cd ~/hr-rag-lab
python ci/rollback_lab.py
```

**Expected:** `Rolled back`, the function name, and the two version numbers, such as `approved moved from version 9 to version 7`.

Running it again swaps back, because each rollback records the version it left. The next passing run on `main` also moves `approved` forward again.

## Evidence to keep

- The branch, pull request and run links for each change.
- The failing and passing trace links.
- The passing report.
- Your explanation of the tool results, and of the release and recovery steps.

**Next:** [09 Tear down](09-tear-down.md)
