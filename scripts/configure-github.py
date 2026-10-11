"""Configure a student's GitHub lab environment from Terraform outputs.

Requires GitHub CLI sign-in and an instructor-provided AWS role restricted to
this exact repository. Secret values use standard input, never command arguments.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def run(arguments, value=None):
    return subprocess.check_output(arguments, input=value, text=True, cwd=ROOT)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True, help='Your GitHub owner/repository')
    parser.add_argument('--role-arn', required=True, help='Instructor-issued role for this repository')
    args = parser.parse_args()
    run(['gh', 'auth', 'status'])
    outputs = json.loads(run(['terraform', '-chdir=infra/terraform', 'output', '-json']))
    def output(name):
        return outputs[name]['value']
    frontend = dict(line.split('=', 1) for line in (ROOT/'frontend/.env.production').read_text().splitlines() if '=' in line)
    keys = dict(line.split('=', 1) for line in (ROOT/'.env.langfuse').read_text(encoding='utf-8-sig').splitlines() if '=' in line and not line.lstrip().startswith('#'))
    keys = {key: value.strip().strip('"').strip("'") for key, value in keys.items()}
    if not keys.get('LANGFUSE_PUBLIC_KEY', '').startswith('pk-lf-') or not keys.get('LANGFUSE_SECRET_KEY', '').startswith('sk-lf-'):
        raise SystemExit('Check the public and secret key fields before configuring GitHub')
    variables = {
        'AWS_REGION': os.environ.get('AWS_REGION', 'us-east-1'),
        'AWS_STAGING_ROLE_ARN': args.role_arn,
        'HR_STAGING_FUNCTION': output('candidate_function'),
        'HR_STAGING_ORIGIN': output('app_url'),
        'HR_TEST_USERS_SECRET_ARN': output('evaluation_users_secret_arn'),
        'HR_COGNITO_POOL_ID': output('cognito_user_pool_id'),
        'HR_COGNITO_CLIENT_ID': output('cognito_client_id'),
        'HR_STAGING_FRONTEND_BUCKET': output('frontend_bucket'),
        'HR_STAGING_DISTRIBUTION_ID': output('cloudfront_distribution_id'),
        'LANGFUSE_BASE_URL': keys['LANGFUSE_BASE_URL'],
        'VITE_COGNITO_AUTHORITY': frontend['VITE_COGNITO_AUTHORITY'],
        'VITE_COGNITO_DOMAIN': frontend['VITE_COGNITO_DOMAIN'],
        'ENABLE_DEEPEVAL': 'true', 'ENABLE_EVIDENTLY': 'true',
    }
    for environment in ['hr-lab-staging', 'hr-production-demo']:
        run(['gh', 'api', '--method', 'PUT', f'repos/{args.repo}/environments/{environment}'])
    for name, value in variables.items():
        run(['gh', 'variable', 'set', name, '--repo', args.repo, '--env', 'hr-lab-staging'], str(value))
    for name in ['LANGFUSE_PUBLIC_KEY', 'LANGFUSE_SECRET_KEY']:
        run(['gh', 'secret', 'set', name, '--repo', args.repo, '--env', 'hr-lab-staging'], keys[name])
    print('GitHub variables and secrets configured. Review environment approvals and main-branch protection in Settings.')
    print('This helper does not create an AWS role, broaden its trust, or configure reviewers.')

if __name__ == '__main__':
    main()
