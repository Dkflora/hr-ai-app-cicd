# 06a3 Add the release jobs

**Goal:** add the two jobs that run after the `candidate` job passes: the production handoff, and the job that tags the release.

Here you only change a file on your computer, like in document 06a2. You commit it in document 06b.

- **`production-handoff-dry-run`** checks the tested commit and its passing report, then prints what production would receive. It changes nothing.
- **`tag-release`** tags the tested commit in Git with its release number from the `VERSION` file, such as `v1.0.0`, and pushes the tag to GitHub. It is the only job allowed to write to the repository (`contents: write`), and it tags a commit only when the release gate passed.

## Step 1: Add the two release jobs

This command adds both jobs to the end of the workflow file. Run it once only.

```bash
cd ~/hr-rag-lab
cat >> .github/workflows/hr-quality.yml <<'EOF'
  # Demonstrate the approval boundary without deploying production infrastructure.
  production-handoff-dry-run:                                           # job
    name: Production handoff (dry run)                                  # job title
    if: github.event_name != 'pull_request' && github.ref == 'refs/heads/main'
    needs: candidate                                                    # depends on candidate
    runs-on: ubuntu-24.04                                               # agent
    environment: hr-production-approval                                 # approval gate
    permissions:                                                        # token rights
      contents: read                                                    # read-only code
    steps:                                                              # steps
      - uses: actions/download-artifact@v8                              # get artifacts
        with:
          name: hr-candidate-evidence                                   # artifact name
          path: evidence                                                # folder
      - name: Verify exact tested release and show production handoff
        env:                                                            # step variables
          EXPECTED_COMMIT: ${{ github.sha }}                            # tested commit
        run: |
          python - <<'PY'
          import json, os
          from pathlib import Path
          release=json.loads(Path('evidence/release.json').read_text())
          report=Path('evidence/report.md').read_text()
          if release['commit'] != os.environ['EXPECTED_COMMIT']:
              raise SystemExit('Release does not match the merged commit')
          if 'Release gate: PASS.' not in report:
              raise SystemExit('A passing evaluation report is required')
          print('DEMONSTRATION ONLY: production would receive the tested backend artifact and exact prompt version.')
          print('React would be built from this same commit with production configuration.')
          print('No production resources or traffic are changed by this dry-run job.')
          PY
  # Name the approved release in Git: tag the tested commit with its VERSION number.
  tag-release:                                                          # job
    name: Tag the approved release                                      # job title
    if: github.event_name != 'pull_request' && github.ref == 'refs/heads/main'  # run condition
    needs: candidate                                                    # depends on candidate
    runs-on: ubuntu-24.04                                               # agent
    permissions:                                                        # token rights
      contents: write                                                   # may push a tag
    steps:                                                              # steps
      - uses: actions/checkout@v7                                       # get code
        with:                                                           # inputs
          fetch-depth: 0                                                # all history and release tags
      - uses: actions/setup-python@v7                                   # install Python
        with:
          python-version: '3.12'
      - uses: actions/download-artifact@v8                              # get artifacts
        with:
          name: hr-candidate-evidence                                   # artifact name
          path: evidence                                                # folder
      - name: Tag the tested commit with its release number             # step title
        env:                                                            # step variables
          EXPECTED_COMMIT: ${{ github.sha }}                            # tested commit
        run: python ci/tag_release.py                                   # create and push the tag
EOF
grep -nE '^  (checks|candidate|production-handoff-dry-run|tag-release):' .github/workflows/hr-quality.yml
```

**Expected:** the last command prints four jobs: `checks` on line 15, `candidate` on line 41, `production-handoff-dry-run` on line 217 and `tag-release` on line 248.

## How to read the new jobs

- `needs: candidate`: both jobs wait for the `candidate` job. If it fails, GitHub skips them. They then run at the same time.
- `environment: hr-production-approval`: the handoff job uses its own environment. In document 06b you can make a person approve it before it runs.
- `actions/download-artifact`: both jobs read the files the `candidate` job saved under **Artifacts**: `release.json` and `report.md`.
- `EXPECTED_COMMIT: ${{ github.sha }}`: the commit this run was started for. Both jobs stop if the saved release came from another commit. They also stop unless the report says `Release gate: PASS.` in full.
- `fetch-depth: 0`: downloads the existing tags, so `ci/tag_release.py` can refuse a release number that is already tagged.

When the handoff job runs, its log ends with three lines. The first starts with `DEMONSTRATION ONLY: production would receive`. The last is `No production resources or traffic are changed by this dry-run job.`

Pushing a tag does not start the workflow again: the workflow runs on pushes to branches only.

If a job name appears twice, you ran a block twice. Create the file again with document 04, step 2, then run the 06a2 block and this block once each.

**Next:** [06b Environments, merge and first run](06b-environments-merge-and-first-run.md)
