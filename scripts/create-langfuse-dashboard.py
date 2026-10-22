"""Create the "HR assistant health" dashboard in your Langfuse project.

    python scripts/create-langfuse-dashboard.py

Run it once. Then open Langfuse, go to Dashboards, and open "HR assistant health".
Running it again is safe: if the dashboard already exists, it changes nothing.

The dashboard shows how the app behaves for real people, not for the pipeline's test
accounts: how many questions they ask, how long answers take per release, what the AI
models cost, how many questions the guardrail blocked, and how people vote on answers.

It uses Langfuse's dashboard API, which Langfuse marks as unstable: a newer Langfuse
version may change it. The keys come from .env.langfuse, the same file the setup used.
"""
import base64
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_NAME = 'HR assistant health'

# Filters shared by the widgets below.
ONE_PER_QUESTION = {'column': 'isRootObservation', 'operator': '=', 'value': True, 'type': 'boolean'}
ANSWERS = {'column': 'name', 'operator': '=', 'value': 'HR answer', 'type': 'string'}
BLOCKED = {'column': 'name', 'operator': '=', 'value': 'Blocked question', 'type': 'string'}
PEOPLE_ONLY = {'column': 'tags', 'operator': 'none of', 'value': ['test-account'], 'type': 'arrayOptions'}
FEEDBACK = {'column': 'name', 'operator': '=', 'value': 'user_feedback', 'type': 'string'}

WIDGETS = [
    {'name': 'Questions per day, real people',
     'description': 'Answered questions, without the pipeline test accounts.',
     'view': 'observations', 'chartType': 'BAR_TIME_SERIES',
     'metrics': [{'measure': 'count', 'agg': 'count'}], 'dimensions': [],
     'filters': [ONE_PER_QUESTION, ANSWERS, PEOPLE_ONLY]},
    {'name': 'Answer time p95 by release (ms)',
     'description': '95% of answers took less than this. Compare releases.',
     'view': 'observations', 'chartType': 'VERTICAL_BAR',
     'metrics': [{'measure': 'latency', 'agg': 'p95'}], 'dimensions': [{'field': 'release'}],
     'filters': [ONE_PER_QUESTION, ANSWERS]},
    {'name': 'AI model cost per day (USD)',
     'description': 'Cost of every model call, by model.',
     'view': 'observations', 'chartType': 'LINE_TIME_SERIES',
     'metrics': [{'measure': 'totalCost', 'agg': 'sum'}], 'dimensions': [{'field': 'providedModelName'}],
     'filters': []},
    {'name': 'Blocked questions per day',
     'description': 'Questions the guardrail stopped, such as ones with a card number.',
     'view': 'observations', 'chartType': 'BAR_TIME_SERIES',
     'metrics': [{'measure': 'count', 'agg': 'count'}], 'dimensions': [],
     'filters': [ONE_PER_QUESTION, BLOCKED]},
    {'name': 'Share of thumbs up',
     'description': 'user_feedback: 1 means every vote was a thumbs up.',
     'view': 'scores-boolean', 'chartType': 'NUMBER',
     'metrics': [{'measure': 'value', 'agg': 'avg'}], 'dimensions': [],
     'filters': [FEEDBACK]},
    {'name': 'Votes: thumbs up and down',
     'description': 'Number of votes of each kind.',
     'view': 'scores-boolean', 'chartType': 'PIE',
     'metrics': [{'measure': 'count', 'agg': 'count'}], 'dimensions': [{'field': 'booleanValue'}],
     'filters': [FEEDBACK]},
]


def read_keys():
    values = {}
    for line in (ROOT / '.env.langfuse').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            key, value = line.split('=', 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


class Langfuse:
    """A few calls to the Langfuse public API, signed in with the project's key pair."""

    def __init__(self, keys):
        self.base = keys.get('LANGFUSE_BASE_URL', 'https://us.cloud.langfuse.com').rstrip('/')
        pair = f"{keys['LANGFUSE_PUBLIC_KEY']}:{keys['LANGFUSE_SECRET_KEY']}"
        self.auth = 'Basic ' + base64.b64encode(pair.encode()).decode()

    def call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(self.base + path, data=data, method=method,
                                         headers={'Authorization': self.auth, 'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)


def main():
    langfuse = Langfuse(read_keys())
    existing = langfuse.call('GET', '/api/public/unstable/dashboards')['data']
    if any(dashboard['name'] == DASHBOARD_NAME for dashboard in existing):
        print(f'The dashboard "{DASHBOARD_NAME}" already exists. Nothing changed.')
        return

    dashboard = langfuse.call('POST', '/api/public/unstable/dashboards', {
        'name': DASHBOARD_NAME,
        'description': 'How the HR assistant behaves for real people: volume, speed, cost, blocks and votes.',
    })
    for number, widget in enumerate(WIDGETS):
        created = langfuse.call('POST', '/api/public/unstable/dashboard-widgets', widget)
        # Two widgets per row on Langfuse's 12-column grid.
        langfuse.call('POST', f"/api/public/unstable/dashboards/{dashboard['id']}/placements", {
            'type': 'widget', 'widgetId': created['id'],
            'x': (number % 2) * 6, 'y': (number // 2) * 6, 'width': 6, 'height': 6,
        })
    print(f'Created the dashboard "{DASHBOARD_NAME}" with {len(WIDGETS)} charts.')
    print('In Langfuse, open Dashboards, then open it.')


if __name__ == '__main__':
    main()
