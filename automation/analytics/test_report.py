from contextlib import contextmanager, redirect_stderr, redirect_stdout
import io
import json
import sys
import types
import unittest
from unittest import mock
from urllib.error import HTTPError, URLError

import report
from report import Authentication, ReportError, authentication, reports, run_report

DATE = '2020-01-02'
SECRET = 'TEST-ONLY-CREDENTIAL-CANARY-do-not-print'
PRIVATE = 'private-traffic-canary@example.test'
PRIVATE_METRIC = '987654321'
SERVICE_INFO = {'type': 'service_account', 'client_email': 'fake@example.iam.gserviceaccount.com',
                'private_key': SECRET, 'token_uri': 'https://oauth2.googleapis.com/token'}
SERVICE_JSON = json.dumps(SERVICE_INFO)


def response_for(body, *, row_count=1, page_size=1):
    return {
        'dimensionHeaders': [{'name': item['name']} for item in body.get('dimensions', [])],
        'metricHeaders': [{'name': item['name'], 'type': 'TYPE_INTEGER'} for item in body['metrics']],
        'rowCount': row_count,
        'rows': [{'dimensionValues': [{'value': PRIVATE} for _ in body.get('dimensions', [])],
                  'metricValues': [{'value': PRIVATE_METRIC} for _ in body['metrics']]}
                 for _ in range(page_size)],
        'metadata': {'timeZone': 'Asia/Tokyo', 'testCanary': PRIVATE},
    }


class FakeResponse:
    def __init__(self, data, status=200):
        self.data, self.status_code = data, status

    def json(self):
        if isinstance(self.data, Exception):
            raise self.data
        return self.data


class FakeSession:
    def __init__(self, handler=None):
        self.handler = handler or (lambda body: FakeResponse(response_for(body)))
        self.calls, self.closed = [], False

    def post(self, url, *, json, timeout, allow_redirects):
        self.calls.append((url, json, timeout, allow_redirects))
        return self.handler(json)

    def close(self):
        self.closed = True


@contextmanager
def fake_google(session=None):
    """No installed SDK, real key, refresh request or network is used by these tests."""
    session = session or FakeSession()
    names = ['google', 'google.oauth2', 'google.oauth2.service_account', 'google.auth',
             'google.auth.transport', 'google.auth.transport.requests']
    modules = {name: types.ModuleType(name) for name in names}
    credentials_factory = mock.Mock(return_value=object())
    session_factory = mock.Mock(return_value=session)
    modules['google.oauth2.service_account'].Credentials = types.SimpleNamespace(
        from_service_account_info=credentials_factory)
    modules['google.auth.transport.requests'].AuthorizedSession = session_factory
    with mock.patch.dict(sys.modules, modules):
        yield credentials_factory, session_factory, session


def cli(args, env=None):
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = report.main(args, {} if env is None else env)
    return code, json.loads(stdout.getvalue()), stdout.getvalue() + stderr.getvalue()


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.body = reports(DATE, DATE)['japan_daily']

    def test_global_inquiries_do_not_exclude_missing_geography(self):
        queries = reports('2026-09-28', '2026-09-28')
        self.assertNotIn('JP', json.dumps(queries['inquiry_events_global']))
        self.assertIn('generate_lead', json.dumps(queries['inquiry_events_global']))
        self.assertIn('JP', json.dumps(queries['inquiry_events_japan']))
        self.assertIn('JP', json.dumps(queries['japan_daily']))

    def test_pagination_preserves_metadata(self):
        calls = []
        def transport(req, timeout):
            body = json.loads(req.data)
            calls.append(body['offset'])
            self.assertEqual(req.full_url, report.ENDPOINT)
            self.assertEqual(req.get_header('Authorization'), 'Bearer test-only')
            self.assertEqual(timeout, 30)
            return io.StringIO(json.dumps(response_for(body, row_count=2)))
        result = run_report(self.body, 'test-only', transport)
        self.assertEqual(calls, ['0', '1'])
        self.assertEqual(len(result['rows']), 2)
        self.assertEqual(result['metadata']['timeZone'], 'Asia/Tokyo')

    def test_incomplete_response_is_not_reported_as_success(self):
        def transport(req, timeout):
            return io.StringIO(json.dumps(response_for(self.body, row_count=1, page_size=0)))
        with self.assertRaisesRegex(ReportError, '^incomplete_response$') as raised:
            run_report(self.body, 'test-only', transport)
        self.assertEqual(raised.exception.detail, 'row_count_mismatch')

    def test_authorized_session_paginates_without_manual_bearer_headers(self):
        session = FakeSession(lambda body: FakeResponse(response_for(body, row_count=2)))
        result = run_report(self.body, session=session)
        self.assertEqual([call[1]['offset'] for call in session.calls], ['0', '1'])
        self.assertTrue(all(call[0] == report.ENDPOINT and call[2:] == (30, False) for call in session.calls))
        self.assertEqual(len(result['rows']), 2)

    def test_empty_report_with_valid_headers_is_valid(self):
        payload = response_for(self.body, row_count=0, page_size=0)
        # Protobuf JSON may omit empty/default fields.
        del payload['rowCount']
        del payload['rows']
        result = run_report(self.body, session=FakeSession(lambda body: FakeResponse(payload)))
        self.assertEqual(result['rows'], [])

    def test_verified_empty_report_accepts_observed_omissions_without_inventing_data(self):
        # Observed response shape: both headers, rows, rowCount and emptyReason
        # are absent, while the report kind and property timezone are present.
        minimal = {'kind': 'analyticsData#runReport',
                   'metadata': {'timeZone': 'Asia/Tokyo'}}
        aggregate_body = dict(self.body, dimensions=[])
        for body in (self.body, aggregate_body):
            complete = response_for(body, row_count=0, page_size=0)
            complete.update(kind=minimal['kind'], metadata=minimal['metadata'])
            variants = [minimal,
                        dict(minimal, metadata={'timeZone': 'Asia/Tokyo', 'emptyReason': ''}),
                        dict(minimal, metadata={'timeZone': 'Asia/Tokyo', 'emptyReason': PRIVATE}),
                        dict(minimal, dimensionHeaders=[], metricHeaders=[], rows=[], rowCount=0,
                             totals=[], maximums=[], minimums=[]),
                        complete,
                        dict(minimal, metricHeaders=complete['metricHeaders'])]
            for payload in variants:
                with self.subTest(dimensions=bool(body['dimensions']), fields=list(payload)):
                    result = run_report(body, session=FakeSession(lambda request: FakeResponse(payload)))
                    self.assertEqual(result, dict(payload, rows=[]))
                    self.assertEqual(result['rows'], [])
        nonempty = response_for(self.body)
        nonempty['kind'] = minimal['kind']
        self.assertEqual(run_report(self.body, session=FakeSession(lambda body: FakeResponse(nonempty))),
                         nonempty)
        private_reason = dict(minimal, metadata={'timeZone': 'Asia/Tokyo', 'emptyReason': PRIVATE})
        with fake_google(FakeSession(lambda body: FakeResponse(private_reason))):
            code, payload, text = cli(['--execute', '--status-only', '--date', DATE],
                                      {'GITHUB_ACTIONS': 'true', 'GSC_SERVICE_ACCOUNT_JSON': SERVICE_JSON})
        self.assertEqual(code, 0)
        self.assertEqual(payload['reportDefinitionsCompleted'], 5)
        for forbidden in (PRIVATE, SECRET, PRIVATE_METRIC, 'emptyReason', 'reports'):
            self.assertNotIn(forbidden, text)

    def test_empty_header_exception_requires_identity_timezone_and_no_contradictory_data(self):
        minimal = {'kind': 'analyticsData#runReport',
                   'metadata': {'timeZone': 'Asia/Tokyo'}}
        missing_kind = dict(minimal)
        del missing_kind['kind']
        invalid = [{}, {'kind': minimal['kind']}, missing_kind,
                   dict(minimal, kind=PRIVATE), dict(minimal, error={'message': SECRET})]
        for timezone in ('', None, 'not/a-time-zone', [SECRET], '/' + SECRET):
            invalid.append(dict(minimal, metadata={'timeZone': timezone}))
        for metadata in ({}, None, PRIVATE):
            invalid.append(dict(minimal, metadata=metadata))
        for reason in (None, [], {'raw': SECRET}, 0, True):
            invalid.append(dict(minimal, metadata={'timeZone': 'Asia/Tokyo', 'emptyReason': reason}))
        for field, value in [('metricHeaders', None), ('metricHeaders', {}),
                             ('metricHeaders', [{'name': PRIVATE}]),
                             ('dimensionHeaders', None),
                             ('dimensionHeaders', [{'name': PRIVATE}]),
                             ('dimensionHeaders', [{'name': [SECRET]}])]:
            invalid.append(dict(minimal, **{field: value}))
        for field, value in [('rows', None), ('rows', {}),
                             ('rows', response_for(self.body)['rows']),
                             ('rowCount', 1), ('rowCount', -1), ('rowCount', '0'),
                             ('rowCount', False), ('rowCount', True),
                             ('totals', response_for(self.body)['rows']),
                             ('maximums', {}), ('minimums', None)]:
            invalid.append(dict(minimal, **{field: value}))
        for payload in invalid:
            with self.subTest(fields=list(payload)):
                with self.assertRaisesRegex(ReportError, '^invalid_response$') as raised:
                    run_report(self.body, session=FakeSession(lambda body: FakeResponse(payload)))
                self.assertIn(raised.exception.detail, report.FAILURE_DETAILS)
                for forbidden in (PRIVATE, SECRET, PRIVATE_METRIC):
                    self.assertNotIn(forbidden, str(raised.exception))
                    self.assertNotIn(forbidden, raised.exception.detail)

    def test_error_envelopes_and_unsupported_success_shapes_fail_closed(self):
        invalid = [(None, 'response_shape'), ([], 'response_shape'), ({}, 'header_shape'),
                   ({'error': {'message': PRIVATE}}, 'response_shape')]
        for field, value, detail in [
                ('rowCount', -1, 'row_count_shape'), ('rowCount', True, 'row_count_shape'),
                ('rowCount', '1', 'row_count_shape'), ('rows', {}, 'rows_shape'),
                ('rows', [PRIVATE], 'rows_shape'), ('metricHeaders', [], 'header_shape'),
                ('dimensionHeaders', PRIVATE, 'header_shape'), ('metadata', PRIVATE, 'metadata_shape')]:
            payload = response_for(self.body)
            payload[field] = value
            invalid.append((payload, detail))
        wrong_header = response_for(self.body)
        wrong_header['metricHeaders'][0]['name'] = PRIVATE
        invalid.append((wrong_header, 'header_mismatch'))
        malformed_header = response_for(self.body)
        malformed_header['metricHeaders'][0]['name'] = [SECRET]
        invalid.append((malformed_header, 'header_shape'))
        wrong_values = response_for(self.body)
        wrong_values['rows'][0]['metricValues'] = [{'value': 1}]
        invalid.append((wrong_values, 'metric_values'))
        wrong_dimensions = response_for(self.body)
        wrong_dimensions['rows'][0]['dimensionValues'] = [{'value': [SECRET]}]
        invalid.append((wrong_dimensions, 'dimension_values'))
        invalid.append((response_for(self.body, row_count=0, page_size=1), 'row_count_mismatch'))
        for payload, detail in invalid:
            with self.subTest(detail=detail):
                with self.assertRaisesRegex(ReportError, '^invalid_response$') as raised:
                    run_report(self.body, session=FakeSession(lambda body: FakeResponse(payload)))
                self.assertEqual(raised.exception.detail, detail)
                for forbidden in (SECRET, PRIVATE, PRIVATE_METRIC):
                    self.assertNotIn(forbidden, str(raised.exception))
                    self.assertNotIn(forbidden, raised.exception.detail)

    def test_transport_details_are_allowlisted_and_survive_error_wrapping(self):
        for payload, status, detail in [(ValueError(SECRET), 200, 'invalid_json'),
                                        (response_for(self.body), PRIVATE, 'http_status')]:
            with self.subTest(detail=detail):
                with self.assertRaisesRegex(ReportError, '^invalid_response$') as raised:
                    run_report(self.body, session=FakeSession(lambda body: FakeResponse(payload, status)))
                self.assertEqual(raised.exception.detail, detail)
        def invalid_json(req, timeout):
            return io.StringIO(SECRET)
        with self.assertRaisesRegex(ReportError, '^invalid_response$') as raised:
            run_report(self.body, 'test-only', invalid_json)
        self.assertEqual(raised.exception.detail, 'invalid_json')
        for detail in (SECRET, [SECRET], {'raw': PRIVATE}, 'header_shape'):
            def fail(body):
                error = ReportError('invalid_response', detail=detail)
                error.args = (SECRET, PRIVATE)
                raise error
            with self.subTest(detail_type=type(detail).__name__):
                with self.assertRaisesRegex(ReportError, '^invalid_response$') as raised:
                    run_report(self.body, session=FakeSession(fail))
                self.assertEqual(raised.exception.detail,
                                 'header_shape' if detail == 'header_shape' else 'validation_failed')
                for forbidden in (SECRET, PRIVATE):
                    self.assertNotIn(forbidden, str(raised.exception))
                    self.assertNotIn(forbidden, raised.exception.detail)

    def test_row_count_change_during_pagination_is_incomplete(self):
        session = FakeSession(lambda body: FakeResponse(response_for(
            body, row_count=2 if body['offset'] == '0' else 3)))
        with self.assertRaisesRegex(ReportError, '^incomplete_response$') as raised:
            run_report(self.body, session=session)
        self.assertEqual(raised.exception.detail, 'row_count_mismatch')

    def test_legacy_http_errors_are_sanitized_and_classified(self):
        payload = {'error': {'message': SECRET, 'details': [
            {'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'SERVICE_DISABLED',
             'metadata': {'testCanary': PRIVATE}}]}}
        def transport(req, timeout):
            raise HTTPError(report.ENDPOINT, 403, SECRET, {}, io.BytesIO(json.dumps(payload).encode()))
        with self.assertRaisesRegex(ReportError, '^api_disabled$'):
            run_report(self.body, 'test-only', transport)


class AuthenticationTests(unittest.TestCase):
    def test_manual_token_has_priority_and_does_not_import_sdk(self):
        with fake_google() as (factory, session_factory, _):
            auth = authentication({'GA4_ACCESS_TOKEN': SECRET,
                                   'GA4_SERVICE_ACCOUNT_JSON': 'invalid',
                                   'GSC_SERVICE_ACCOUNT_JSON': 'invalid'})
            self.assertEqual(auth.mode, 'access_token')
            self.assertEqual(auth.token, SECRET)
            self.assertIsNone(auth.session)
            self.assertNotIn(SECRET, repr(auth))
            factory.assert_not_called()
            session_factory.assert_not_called()

    def test_service_account_precedence_readonly_scope_and_refresh_session(self):
        for env, expected in [
                ({'GA4_SERVICE_ACCOUNT_JSON': SERVICE_JSON, 'GSC_SERVICE_ACCOUNT_JSON': 'invalid'}, 'ga4_service_account'),
                ({'GSC_SERVICE_ACCOUNT_JSON': SERVICE_JSON}, 'gsc_service_account')]:
            with self.subTest(mode=expected), fake_google() as (factory, session_factory, session):
                auth = authentication(env)
                self.assertEqual(auth.mode, expected)
                self.assertIs(auth.session, session)
                self.assertIsNone(auth.token)
                factory.assert_called_once_with(SERVICE_INFO, scopes=[report.READONLY_SCOPE])
                session_factory.assert_called_once_with(factory.return_value, refresh_timeout=30)

    def test_invalid_selected_credentials_do_not_fall_back_to_another_identity(self):
        with fake_google() as (factory, _, _):
            with self.assertRaisesRegex(ReportError, '^invalid_credentials$'):
                authentication({'GA4_SERVICE_ACCOUNT_JSON': SECRET, 'GSC_SERVICE_ACCOUNT_JSON': SERVICE_JSON})
            factory.assert_not_called()

    def test_unsupported_credentials_and_token_destinations_fail_before_sdk_use(self):
        variants = [[], {}, dict(SERVICE_INFO, type='authorized_user'),
                    dict(SERVICE_INFO, token_uri='https://example.test/token'),
                    dict(SERVICE_INFO, universe_domain='example.test'),
                    dict(SERVICE_INFO, private_key=None)]
        for info in variants:
            with self.subTest(info_type=type(info).__name__), fake_google() as (factory, _, _):
                with self.assertRaisesRegex(ReportError, '^invalid_credentials$'):
                    authentication({'GA4_SERVICE_ACCOUNT_JSON': json.dumps(info)})
                factory.assert_not_called()

    def test_missing_credentials_and_invalid_token_have_safe_codes(self):
        for env, code in [({}, 'missing_credentials'),
                          ({'GA4_ACCESS_TOKEN': SECRET + '\n'}, 'invalid_credentials')]:
            with self.assertRaisesRegex(ReportError, '^' + code + '$'):
                authentication(env)

    def test_dependency_and_key_parse_errors_do_not_expose_exception_messages(self):
        original_import = __import__
        def unavailable(name, *args, **kwargs):
            if name.startswith('google.'):
                raise ImportError(SECRET)
            return original_import(name, *args, **kwargs)
        with mock.patch('builtins.__import__', side_effect=unavailable):
            code, payload, text = cli(['--execute', '--status-only', '--date', DATE],
                                      {'GA4_SERVICE_ACCOUNT_JSON': SERVICE_JSON})
        self.assertEqual(code, 1)
        self.assertEqual(payload['error'], 'missing_dependency')
        self.assertNotIn(SECRET, text)
        with fake_google() as (factory, _, _):
            factory.side_effect = ValueError(SECRET)
            code, payload, text = cli(['--execute', '--status-only', '--date', DATE],
                                      {'GA4_SERVICE_ACCOUNT_JSON': SERVICE_JSON})
        self.assertEqual(code, 1)
        self.assertEqual(payload['error'], 'invalid_credentials')
        self.assertNotIn(SECRET, text)


class CommandTests(unittest.TestCase):
    def assert_private_values_absent(self, text):
        for value in [SECRET, PRIVATE, PRIVATE_METRIC, 'Traceback']:
            self.assertNotIn(value, text)

    def test_default_preview_needs_neither_authentication_nor_network(self):
        with mock.patch('report.authentication') as auth, mock.patch('report.run_report') as execute:
            code, payload, text = cli(['--date', DATE], {'GA4_ACCESS_TOKEN': SECRET})
        self.assertEqual(code, 0)
        self.assertEqual(payload['mode'], 'request_preview')
        self.assertEqual(len(payload['reports']), 5)
        auth.assert_not_called()
        execute.assert_not_called()
        self.assert_private_values_absent(text)

    def test_status_only_fetches_all_five_definitions_but_emits_no_analytics_values(self):
        with fake_google() as (_, _, session):
            code, payload, text = cli(['--execute', '--status-only', '--date', DATE],
                                      {'GITHUB_ACTIONS': 'true', 'GSC_SERVICE_ACCOUNT_JSON': SERVICE_JSON})
        self.assertEqual(code, 0)
        self.assertEqual(payload['status'], 'ok')
        self.assertEqual(payload['authMode'], 'gsc_service_account')
        self.assertEqual(payload['reportDate'], DATE)
        self.assertEqual(payload['reportDefinitionsCompleted'], 5)
        self.assertEqual(set(payload), {'status', 'authMode', 'reportDate', 'checkedAt', 'reportDefinitionsCompleted'})
        self.assertEqual(len(session.calls), 5)
        self.assertTrue(session.closed)
        self.assert_private_values_absent(text)

    def test_incomplete_run_is_all_or_nothing_for_both_output_modes(self):
        for extra in [[], ['--status-only']]:
            session = FakeSession()
            def handler(body):
                return FakeResponse(response_for(body, page_size=0 if len(session.calls) == 3 else 1))
            session.handler = handler
            with self.subTest(extra=extra), fake_google(session):
                code, payload, text = cli(['--execute', '--date', DATE] + extra,
                                          {'GA4_SERVICE_ACCOUNT_JSON': SERVICE_JSON})
            self.assertEqual(code, 1)
            self.assertEqual(payload['error'], 'incomplete_response')
            self.assertEqual(payload['reportDefinitionsCompleted'], 0)
            self.assertNotIn('reports', payload)
            self.assertEqual(len(session.calls), 3)
            self.assertTrue(session.closed)
            self.assert_private_values_absent(text)

    def test_raw_execute_is_refused_in_github_actions_before_authentication(self):
        with mock.patch('report.authentication') as auth, mock.patch('report.run_report') as execute:
            code, payload, text = cli(['--execute', '--date', DATE],
                                      {'GITHUB_ACTIONS': 'true', 'GA4_ACCESS_TOKEN': SECRET})
        self.assertEqual(code, 1)
        self.assertEqual(payload['error'], 'raw_output_forbidden_in_ci')
        auth.assert_not_called()
        execute.assert_not_called()
        self.assert_private_values_absent(text)

    def test_safe_http_failure_classification_and_no_server_message_output(self):
        cases = [(401, 'invalid_token'), (403, 'access_denied'), (429, 'rate_limited'),
                 (503, 'network_error'), (400, 'api_error')]
        for status, expected in cases:
            session = FakeSession(lambda body: FakeResponse({'error': {'message': SECRET}}, status))
            with self.subTest(status=status), fake_google(session):
                code, payload, text = cli(['--execute', '--status-only', '--date', DATE],
                                          {'GSC_SERVICE_ACCOUNT_JSON': SERVICE_JSON})
            self.assertEqual(code, 1)
            self.assertEqual(payload['error'], expected)
            self.assertEqual(payload['reportDefinitionsCompleted'], 0)
            self.assert_private_values_absent(text)
        disabled = {'error': {'message': PRIVATE, 'details': [
            {'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'SERVICE_DISABLED',
             'metadata': {'testCanary': SECRET}}]}}
        with fake_google(FakeSession(lambda body: FakeResponse(disabled, 403))):
            code, payload, text = cli(['--execute', '--status-only', '--date', DATE],
                                      {'GSC_SERVICE_ACCOUNT_JSON': SERVICE_JSON})
        self.assertEqual(code, 1)
        self.assertEqual(payload['error'], 'api_disabled')
        self.assert_private_values_absent(text)

    def test_network_refresh_and_unexpected_errors_are_fixed_safe_codes(self):
        refresh_error = type('RefreshError', (Exception,), {'__module__': 'google.auth.exceptions'})
        transport_error = type('TransportError', (Exception,), {'__module__': 'google.auth.exceptions'})
        for failure, expected in [(URLError(SECRET), 'network_error'),
                                  (transport_error(SECRET), 'network_error'),
                                  (refresh_error(SECRET), 'invalid_credentials'),
                                  (RuntimeError(SECRET), 'unexpected_error')]:
            def fail(body):
                raise failure
            with self.subTest(expected=expected), fake_google(FakeSession(fail)):
                code, payload, text = cli(['--execute', '--status-only', '--date', DATE],
                                          {'GSC_SERVICE_ACCOUNT_JSON': SERVICE_JSON})
            self.assertEqual(code, 1)
            self.assertEqual(payload['error'], expected)
            self.assertNotIn('detail', payload)
            self.assert_private_values_absent(text)

    def test_malformed_success_and_http_bodies_never_become_success(self):
        for data, status, expected in [(ValueError(SECRET), 200, 'invalid_response'),
                                       (ValueError(SECRET), 403, 'access_denied'),
                                       ({'error': {'message': SECRET}}, 200, 'invalid_response'),
                                       ({}, 200, 'invalid_response')]:
            with self.subTest(status=status, expected=expected), fake_google(FakeSession(lambda body: FakeResponse(data, status))):
                code, payload, text = cli(['--execute', '--status-only', '--date', DATE],
                                          {'GSC_SERVICE_ACCOUNT_JSON': SERVICE_JSON})
            self.assertEqual(code, 1)
            self.assertEqual(payload['error'], expected)
            self.assert_private_values_absent(text)

    def test_local_raw_output_remains_explicit_and_complete(self):
        with fake_google():
            code, payload, _ = cli(['--execute', '--date', DATE], {'GA4_SERVICE_ACCOUNT_JSON': SERVICE_JSON})
        self.assertEqual(code, 0)
        self.assertEqual(set(payload['reports']), set(reports(DATE, DATE)))
        self.assertEqual(payload['reports']['japan_daily']['rows'][0]['metricValues'][0]['value'], PRIVATE_METRIC)

    def test_invalid_cli_and_credential_values_are_not_echoed(self):
        for args, env, expected in [
                (['--status-only'], {}, 'invalid_arguments'),
                (['--date', SECRET], {}, 'invalid_arguments'),
                (['--' + SECRET], {}, 'invalid_arguments'),
                (['--execute', '--status-only'], {}, 'missing_credentials'),
                (['--execute', '--status-only'], {'GA4_SERVICE_ACCOUNT_JSON': SECRET}, 'invalid_credentials')]:
            with self.subTest(expected=expected):
                code, payload, text = cli(args, env)
                self.assertEqual(code, 1)
                self.assertEqual(payload['error'], expected)
                self.assert_private_values_absent(text)


if __name__ == '__main__':
    unittest.main()
