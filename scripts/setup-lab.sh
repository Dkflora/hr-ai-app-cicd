#!/usr/bin/env bash
# One instructor/student setup command, running Terraform plus application bootstrap.
set -euo pipefail
cd "$(dirname "$0")/.."
# Windows has a python3 placeholder that only opens the Microsoft Store, so test that it runs.
if python3 -c '' 2>/dev/null; then PYTHON=python3; else PYTHON=python; fi
"$PYTHON" -m venv .venv
# macOS and Linux put the activate script in bin/, Windows in Scripts/.
if [ -f .venv/Scripts/activate ]; then source .venv/Scripts/activate; else source .venv/bin/activate; fi
python -m pip install -r ci/requirements.txt
command -v aws >/dev/null
command -v terraform >/dev/null
command -v npm >/dev/null
export TF_VAR_langfuse_base_url=$(python -c "from pathlib import Path; d=dict(l.split('=',1) for l in Path('.env.langfuse').read_text().splitlines() if '=' in l and not l.startswith('#')); print(d['LANGFUSE_BASE_URL'].strip().strip(chr(34)).strip(chr(39)))")
test -f infra/terraform/terraform.tfvars || { echo 'Create lab-specific terraform.tfvars first.'; exit 1; }
aws sts get-caller-identity --query Account --output text > /dev/null
bash scripts/build-layer.sh
python ci/release.py
terraform -chdir=infra/terraform init
terraform -chdir=infra/terraform apply
terraform -chdir=infra/terraform output -json > build/terraform-outputs.json
SETUP=$(python -c "import json;print(json.load(open('build/terraform-outputs.json'))['function_names']['value']['setup-db'])")
aws lambda invoke --function-name "$SETUP" --cli-read-timeout 300 --output json build/setup-result.json > build/setup-meta.json
python -c "import json; m=json.load(open('build/setup-meta.json')); r=json.load(open('build/setup-result.json')); failed='FunctionError' in m or (isinstance(r,dict) and 'errorMessage' in r); exit('Database setup failed') if failed else None"
python scripts/initialize-gateway.py
DOCS=$(terraform -chdir=infra/terraform output -raw documents_bucket)
aws s3 cp lambda/data/documents/ "s3://$DOCS/" --recursive --exclude manifest.json
aws s3 cp lambda/data/documents/manifest.json "s3://$DOCS/"
# Uploading the manifest starts ingestion. The verification stage must confirm it finishes.
terraform -chdir=infra/terraform output -raw frontend_env > frontend/.env.production
npm --prefix frontend ci
npm --prefix frontend run build
FRONT=$(terraform -chdir=infra/terraform output -raw frontend_bucket)
aws s3 sync frontend/dist/ "s3://$FRONT/" --exclude index.html --cache-control 'public,max-age=31536000,immutable'
aws s3 cp frontend/dist/index.html "s3://$FRONT/index.html" --cache-control 'no-cache'
DIST=$(terraform -chdir=infra/terraform output -raw cloudfront_distribution_id)
# Git Bash on Windows rewrites arguments that start with / into Windows paths; this turns that off.
MSYS_NO_PATHCONV=1 aws cloudfront create-invalidation --distribution-id "$DIST" --paths '/index.html' '/'
python scripts/create-test-users.py
python scripts/configure-langfuse.py
python scripts/verify-readiness.py
terraform -chdir=infra/terraform output -raw app_url
