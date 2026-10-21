"""Tests for the app's tracing code, lambda/app/telemetry.py.

How tracing works in this app:
  - @observed('name') above a function records each call as a "span": one timed step.
  - Each span is printed as one JSON line. Lambda sends printed lines to CloudWatch Logs.
  - A separate exporter Lambda forwards those lines to Langfuse.

Most of these tests are privacy tests. A span must never contain a token, a raw tool
result, an error message or an employee ID. Each test captures what the code prints
and checks it.
"""
import contextlib
import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# The code under test lives in lambda/app, so add lambda/ to the import path.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lambda'))

from app.telemetry import observed, redact, conversation_context

# Tracing is off unless this variable is set, so every test turns it on.
TRACING_ON = {'HR_TRACING_ENABLED': 'true'}


def printed_spans(captured_output):
    """Turn the captured printout (one JSON line per span) into a list of spans."""
    spans = []
    for line in captured_output.getvalue().splitlines():
        spans.append(json.loads(line)['span'])
    return spans


def span_attributes(span):
    """Return a span's text attributes as a plain dict, for example {'langfuse.session.id': '...'}."""
    attributes = {}
    for attribute in span['attributes']:
        attributes[attribute['key']] = attribute['value'].get('stringValue')
    return attributes


class TelemetryTests(unittest.TestCase):

    def test_nested_spans_share_trace_and_hide_arguments(self):
        # A request that calls a tool should produce two spans in the same trace,
        # with the tool span as the child of the request span.
        @observed('tool', 'tool')
        def tool(name, secret):
            return 'sensitive-output'

        @observed('request', 'agent')
        def request():
            return tool('lookup', 'private-token')

        captured = io.StringIO()
        with patch.dict(os.environ, TRACING_ON), contextlib.redirect_stdout(captured):
            request()

        # The inner function finishes first, so its span is printed first.
        tool_span, request_span = printed_spans(captured)
        self.assertEqual(tool_span['traceId'], request_span['traceId'])
        self.assertEqual(tool_span['parentSpanId'], request_span['spanId'])
        # The function's argument and its result must not appear anywhere in the output.
        self.assertNotIn('private-token', captured.getvalue())
        self.assertNotIn('sensitive-output', captured.getvalue())

    def test_exception_trace_does_not_copy_error_text(self):
        # An error message can contain private data, so the span records only that the
        # call failed (status code 2 means error), never the message itself.
        @observed('fails')
        def fail():
            raise ValueError('private-token')

        captured = io.StringIO()
        with patch.dict(os.environ, TRACING_ON), contextlib.redirect_stdout(captured), \
             self.assertRaises(ValueError):
            fail()

        self.assertNotIn('private-token', captured.getvalue())
        span = printed_spans(captured)[0]
        self.assertEqual(span['status']['code'], 2)

    def test_common_credential_patterns_are_redacted(self):
        # redact() replaces anything that looks like a credential before it is traced.
        self.assertEqual(redact('Bearer abc.def.ghi'), '[REDACTED]')       # a sign-in token
        self.assertEqual(redact('sk-lf-example-secret'), '[REDACTED]')     # a Langfuse secret key

    def test_conversation_groups_all_spans_and_resets_between_requests(self):
        # conversation_context() tags every span with a session ID, so Langfuse shows one
        # conversation as one session. Each root() call below prints two spans.
        @observed('child')
        def child():
            return 'ok'

        @observed('root')
        def root():
            return child()

        captured = io.StringIO()
        with patch.dict(os.environ, TRACING_ON), contextlib.redirect_stdout(captured):
            with conversation_context('synthetic-employee', 42):
                root()      # spans 1-2
                root()      # spans 3-4: same employee, same conversation
            with conversation_context('other-employee', 42):
                root()      # spans 5-6: a different employee
            root()          # spans 7-8: outside any conversation

        attributes = [span_attributes(span) for span in printed_spans(captured)]
        first_conversation = {a['langfuse.session.id'] for a in attributes[0:4]}
        self.assertEqual(len(first_conversation), 1)        # spans 1-4 share one session
        self.assertNotEqual(attributes[0]['langfuse.session.id'],
                            attributes[4]['langfuse.session.id'])   # other employee, other session
        self.assertNotIn('langfuse.session.id', attributes[-1])     # no conversation, no session
        # The session ID is a hash (SHA-256) of the employee and conversation IDs,
        # so the employee ID itself never appears.
        self.assertNotIn('synthetic-employee', captured.getvalue())

    def test_generation_links_exact_numeric_prompt_version(self):
        # A model call ('generation') is labelled with the prompt version and the commit,
        # so Langfuse can show which prompt and which code produced each answer.
        @observed('model', 'generation')
        def model():
            return 'ok'

        # release_identity() normally reads the deployed release record. Here it returns fixed values.
        identity = {'x-hr-commit': 'source-hash',
                    'x-hr-prompt-sha256': 'prompt-hash',
                    'x-hr-prompt-version': '5'}
        captured = io.StringIO()
        with patch.dict(os.environ, TRACING_ON), \
             patch('app.telemetry.release_identity', return_value=identity), \
             contextlib.redirect_stdout(captured):
            model()

        span = json.loads(captured.getvalue())['span']
        attributes = {a['key']: a['value'] for a in span['attributes']}
        self.assertEqual(attributes['langfuse.version']['stringValue'], 'hr-policy-system v5')
        # Langfuse links a trace to a prompt only when the version is sent as a number.
        self.assertEqual(attributes['langfuse.observation.prompt.version'], {'intValue': '5'})
        self.assertEqual(attributes['langfuse.release']['stringValue'], 'source-hash')


if __name__ == '__main__':
    unittest.main()
