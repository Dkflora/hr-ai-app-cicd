"""Put every recent thumbs-down answer in a Langfuse review queue.

    python scripts/review-thumbs-down.py            thumbs down from the last 7 days
    python scripts/review-thumbs-down.py --days 30

The first run also creates what the review needs in Langfuse. Running it again is safe:
it reuses both, and never adds the same answer twice.
- A score config, failure_cause: the reviewer picks why the answer went wrong.
- An annotation queue, "Thumbs-down review": the list of answers waiting for a reviewer.

It reads the Langfuse keys from .env.langfuse, the same file the setup used.
"""
import argparse
import base64
import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE_NAME = 'Thumbs-down review'
CONFIG_NAME = 'failure_cause'
# The usual causes of a wrong answer, and one for answers that were right but disliked.
CAUSES = ['retrieval', 'prompt', 'model', 'policy_gap', 'not_wrong']


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

    def call(self, method, path, body=None, **query):
        url = self.base + path
        if query:
            url += '?' + urllib.parse.urlencode(query)
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(url, data=data, method=method,
                                         headers={'Authorization': self.auth, 'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)


def failure_cause_config(langfuse):
    """Find the failure_cause score config, or create it."""
    for config in langfuse.call('GET', '/api/public/score-configs', limit=100)['data']:
        if config['name'] == CONFIG_NAME and not config.get('isArchived'):
            return config['id']
    config = langfuse.call('POST', '/api/public/score-configs', {
        'name': CONFIG_NAME,
        'dataType': 'CATEGORICAL',
        'categories': [{'label': cause, 'value': number} for number, cause in enumerate(CAUSES)],
        'description': 'Why the answer went wrong: retrieval missed the passage, the prompt misled the model, '
                       'the model misread the passage, the policy has no answer, or the answer was not wrong.',
    })
    print(f'Created score config {CONFIG_NAME}')
    return config['id']


def review_queue(langfuse, config_id):
    """Find the review queue, or create it."""
    for queue in langfuse.call('GET', '/api/public/annotation-queues', limit=100)['data']:
        if queue['name'] == QUEUE_NAME:
            return queue['id']
    queue = langfuse.call('POST', '/api/public/annotation-queues', {
        'name': QUEUE_NAME,
        'description': 'Answers people marked as not helpful. Read the trace, then pick the failure cause.',
        'scoreConfigIds': [config_id],
    })
    print(f'Created annotation queue "{QUEUE_NAME}"')
    return queue['id']


def thumbs_down_traces(langfuse, days):
    """Trace IDs of the answers that got a thumbs down in the last `days` days."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')
    scores = langfuse.call('GET', '/api/public/v3/scores', name='user_feedback', dataType='BOOLEAN',
                           value='false', fields='subject', fromTimestamp=since, limit=100)['data']
    return [score['subject']['id'] for score in scores if score.get('subject', {}).get('kind') == 'trace']


def main():
    parser = argparse.ArgumentParser(description='Queue recent thumbs-down answers for review in Langfuse.')
    parser.add_argument('--days', type=int, default=7, help='how far back to look (default 7)')
    args = parser.parse_args()

    langfuse = Langfuse(read_keys())
    queue_id = review_queue(langfuse, failure_cause_config(langfuse))

    already_queued = {item['objectId'] for item in langfuse.call(
        'GET', f'/api/public/annotation-queues/{queue_id}/items', limit=100)['data']}
    traces = thumbs_down_traces(langfuse, args.days)
    added = 0
    for trace_id in traces:
        if trace_id not in already_queued:
            langfuse.call('POST', f'/api/public/annotation-queues/{queue_id}/items',
                          {'objectId': trace_id, 'objectType': 'TRACE'})
            added += 1

    print(f'Thumbs down in the last {args.days} days: {len(traces)}. Newly queued: {added}.')
    print(f'In Langfuse, open the "{QUEUE_NAME}" annotation queue to review them.')


if __name__ == '__main__':
    main()
