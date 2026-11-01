#!/usr/bin/env python3
"""Read-only GA4 follow-up. Prints request definitions unless --execute is supplied.

No credentials or report results are written to this public repository.
"""
import argparse
from dataclasses import dataclass, field
import json
import os
import sys
from datetime import date, datetime, timedelta
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

PROPERTY = '547125968'
ENDPOINT = f'https://analyticsdata.googleapis.com/v1beta/properties/{PROPERTY}:runReport'
READONLY_SCOPE = 'https://www.googleapis.com/auth/analytics.readonly'
AUTH_MODES = {'none', 'access_token', 'ga4_service_account', 'gsc_service_account'}
FAILURES = {
    'missing_credentials', 'invalid_credentials', 'missing_dependency',
    'api_disabled', 'access_denied', 'invalid_token', 'rate_limited',
    'network_error', 'incomplete_response', 'invalid_response', 'api_error',
    'raw_output_forbidden_in_ci', 'invalid_arguments', 'unexpected_error',
}
FAILURE_DETAILS = {
    'validation_failed', 'response_shape', 'header_shape', 'header_mismatch',
    'rows_shape', 'row_count_shape', 'metadata_shape', 'dimension_values',
    'metric_values', 'row_count_mismatch', 'invalid_json', 'http_status',
}


class ReportError(RuntimeError):
    """Carries a fixed public error code, never a response or credential value."""
    def __init__(self, code, *, detail='validation_failed'):
        self.code = code if code in FAILURES else 'unexpected_error'
        self.detail = (detail if isinstance(detail, str) and detail in FAILURE_DETAILS
                       else 'validation_failed')
        super().__init__(self.code)


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's normal error may echo arbitrary command-line values.
        raise ReportError('invalid_arguments')


@dataclass
class Authentication:
    mode: str
    token: str | None = field(default=None, repr=False)
    session: object | None = field(default=None, repr=False)


def auth_mode(environ):
    for key, mode in [('GA4_ACCESS_TOKEN', 'access_token'),
                      ('GA4_SERVICE_ACCOUNT_JSON', 'ga4_service_account'),
                      ('GSC_SERVICE_ACCOUNT_JSON', 'gsc_service_account')]:
        if environ.get(key):
            return mode
    return 'none'


def authentication(environ):
    mode = auth_mode(environ)
    if mode == 'none':
        raise ReportError('missing_credentials')
    if mode == 'access_token':
        token = environ['GA4_ACCESS_TOKEN']
        if not isinstance(token, str) or not token.strip() or '\n' in token or '\r' in token:
            raise ReportError('invalid_credentials')
        return Authentication(mode, token=token.strip())
    key = 'GA4_SERVICE_ACCOUNT_JSON' if mode == 'ga4_service_account' else 'GSC_SERVICE_ACCOUNT_JSON'
    try:
        info = json.loads(environ[key])
        if (not isinstance(info, dict) or info.get('type') != 'service_account'
                or info.get('token_uri') != 'https://oauth2.googleapis.com/token'
                or info.get('universe_domain', 'googleapis.com') != 'googleapis.com'
                or not isinstance(info.get('client_email'), str) or not info['client_email']
                or not isinstance(info.get('private_key'), str) or not info['private_key']):
            raise ValueError()
    except (TypeError, ValueError, KeyError):
        raise ReportError('invalid_credentials') from None
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import AuthorizedSession
    except ImportError:
        raise ReportError('missing_dependency') from None
    try:
        credentials = service_account.Credentials.from_service_account_info(
            info, scopes=[READONLY_SCOPE])
        # AuthorizedSession obtains and refreshes access tokens in memory.
        session = AuthorizedSession(credentials, refresh_timeout=30)
        return Authentication(mode, session=session)
    except Exception:
        raise ReportError('invalid_credentials') from None


def http_error_code(status, payload=None):
    error = payload.get('error') if isinstance(payload, dict) else None
    details = error.get('details', []) if isinstance(error, dict) else []
    if isinstance(details, list) and any(
            isinstance(item, dict)
            and item.get('@type') == 'type.googleapis.com/google.rpc.ErrorInfo'
            and item.get('reason') == 'SERVICE_DISABLED'
            for item in details):
        return 'api_disabled'
    if status == 401:
        return 'invalid_token'
    if status == 403:
        return 'access_denied'
    if status == 429:
        return 'rate_limited'
    if isinstance(status, int) and 500 <= status <= 599:
        return 'network_error'
    return 'api_error'


def exception_code(error):
    if isinstance(error, ReportError):
        return error.code
    if isinstance(error, HTTPError):
        try:
            payload = json.loads(error.read(65536))
        except Exception:
            payload = None
        return http_error_code(error.code, payload)
    # Do not stringify exceptions: OAuth and HTTP errors can contain secrets.
    module, name = type(error).__module__, type(error).__name__
    if module.startswith('google.auth') and name in {'RefreshError', 'MalformedError', 'DefaultCredentialsError'}:
        return 'invalid_credentials'
    if (isinstance(error, OSError)
            or module.startswith('requests.exceptions')
            or (module.startswith('google.auth') and name == 'TransportError')):
        return 'network_error'
    return 'unexpected_error'


def exact(field, value):
    return {'filter': {'fieldName': field, 'stringFilter': {'matchType': 'EXACT', 'value': value}}}


def reports(start, end):
    def request(dimensions, metrics, filters=None):
        body = {'dateRanges': [{'startDate': start, 'endDate': end}],
                'dimensions': [{'name': v} for v in dimensions],
                'metrics': [{'name': v} for v in metrics], 'limit': '10000'}
        if filters:
            body['dimensionFilter'] = filters
        return body
    japan = exact('countryId', 'JP')
    inquiry = {'filter': {'fieldName': 'eventName', 'inListFilter': {
        'values': ['contact_form_click', 'generate_lead']}}}
    return {
        'japan_daily': request(['date'], ['activeUsers', 'sessions', 'screenPageViews', 'engagedSessions'], japan),
        'japan_sources': request(['sessionSourceMedium'], ['sessions', 'engagedSessions'], japan),
        'japan_pricing': request(['date', 'pagePath'], ['screenPageViews', 'activeUsers'],
            {'andGroup': {'expressions': [japan, {'filter': {'fieldName': 'pagePath',
                'inListFilter': {'values': ['/ai-video-price', '/ai-video-price.html']}}}]}}),
        # Global first: missing geography on server events must not hide inquiries.
        'inquiry_events_global': request(['dateHourMinute', 'eventName', 'sessionSourceMedium', 'countryId'], ['eventCount'], inquiry),
        'inquiry_events_japan': request(['dateHourMinute', 'eventName', 'sessionSourceMedium'], ['eventCount'],
            {'andGroup': {'expressions': [japan, inquiry]}}),
    }


def validate_page(result, body):
    """Reject error envelopes and unsupported shapes before counting a definition."""
    if not isinstance(result, dict) or 'error' in result:
        raise ReportError('invalid_response', detail='response_shape')
    dimensions = result.get('dimensionHeaders', [])
    metrics = result.get('metricHeaders')
    page = result.get('rows', [])
    count = result.get('rowCount', 0)
    if not isinstance(dimensions, list) or not isinstance(metrics, list) or not metrics:
        raise ReportError('invalid_response', detail='header_shape')
    if not isinstance(page, list):
        raise ReportError('invalid_response', detail='rows_shape')
    if type(count) is not int or count < 0:
        raise ReportError('invalid_response', detail='row_count_shape')
    if 'metadata' in result and not isinstance(result['metadata'], dict):
        raise ReportError('invalid_response', detail='metadata_shape')
    for headers in [dimensions, metrics]:
        if any(not isinstance(header, dict) or not isinstance(header.get('name'), str)
               or not header['name'] for header in headers):
            raise ReportError('invalid_response', detail='header_shape')
    if ([header['name'] for header in dimensions] != [item['name'] for item in body.get('dimensions', [])]
            or [header['name'] for header in metrics] != [item['name'] for item in body.get('metrics', [])]):
        raise ReportError('invalid_response', detail='header_mismatch')
    for row in page:
        if not isinstance(row, dict):
            raise ReportError('invalid_response', detail='rows_shape')
        for key, length in [('dimensionValues', len(dimensions)), ('metricValues', len(metrics))]:
            values = row.get(key, [])
            if (not isinstance(values, list) or len(values) != length
                    or any(not isinstance(value, dict) or not isinstance(value.get('value'), str)
                           for value in values)):
                detail = 'dimension_values' if key == 'dimensionValues' else 'metric_values'
                raise ReportError('invalid_response', detail=detail)
    return page, count


def run_report(body, token=None, transport=urlopen, *, session=None):
    rows, metadata, offset, expected_count = [], None, 0, None
    while True:
        request_body = dict(body, offset=str(offset))
        try:
            if session is not None:
                response = session.post(ENDPOINT, json=request_body, timeout=30, allow_redirects=False)
                status = response.status_code
                try:
                    result = response.json()
                except (TypeError, ValueError):
                    if type(status) is int and status >= 400:
                        raise ReportError(http_error_code(status)) from None
                    raise ReportError('invalid_response', detail='invalid_json') from None
                if type(status) is not int or not 200 <= status < 300:
                    if type(status) is int and status >= 400:
                        raise ReportError(http_error_code(status, result))
                    raise ReportError('invalid_response', detail='http_status')
            else:
                req = Request(ENDPOINT, data=json.dumps(request_body).encode(), headers={
                    'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}, method='POST')
                with transport(req, timeout=30) as response:
                    result = json.load(response)
        except (json.JSONDecodeError, UnicodeError):
            raise ReportError('invalid_response', detail='invalid_json') from None
        except Exception as error:
            detail = error.detail if isinstance(error, ReportError) else 'validation_failed'
            raise ReportError(exception_code(error), detail=detail) from None
        page, count = validate_page(result, body)
        if expected_count is None:
            expected_count = count
        elif count != expected_count:
            raise ReportError('incomplete_response', detail='row_count_mismatch')
        if metadata is None:
            metadata = {k: v for k, v in result.items() if k != 'rows'}
        rows.extend(page)
        if len(rows) > count:
            raise ReportError('invalid_response', detail='row_count_mismatch')
        if len(rows) == count:
            return dict(metadata, rows=rows)
        if not page:
            raise ReportError('incomplete_response', detail='row_count_mismatch')
        offset += len(page)


def connection_status(status, mode, report_date, completed=0, error=None):
    result = {'status': 'ok' if status == 'ok' else 'error',
              'authMode': mode if mode in AUTH_MODES else 'none',
              'reportDate': report_date,
              'checkedAt': datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(),
              'reportDefinitionsCompleted': completed if status == 'ok' else 0}
    if error is not None:
        result['error'] = error if error in FAILURES else 'unexpected_error'
    return result


def main(argv=None, environ=None):
    environ = os.environ if environ is None else environ
    parser = SafeArgumentParser(description=__doc__)
    parser.add_argument('--date', help='Inquiry date, YYYY-MM-DD; default: 2 days ago in Japan')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--status-only', action='store_true', help='Execute all definitions, emitting connection status only')
    auth, mode, report_date = None, 'none', None
    try:
        args = parser.parse_args(argv)
        today = datetime.now(ZoneInfo('Asia/Tokyo')).date()
        try:
            target = date.fromisoformat(args.date) if args.date else today - timedelta(days=2)
        except ValueError:
            raise ReportError('invalid_arguments') from None
        if target > today or (args.status_only and not args.execute):
            raise ReportError('invalid_arguments')
        report_date = target.isoformat()
        bodies = reports(report_date, report_date)
        if not args.execute:
            print(json.dumps({'mode': 'request_preview', 'property': PROPERTY, 'reports': bodies}, ensure_ascii=False, indent=2))
            return 0
        if environ.get('GITHUB_ACTIONS', '').lower() == 'true' and not args.status_only:
            raise ReportError('raw_output_forbidden_in_ci')
        mode = auth_mode(environ)
        auth = authentication(environ)
        output = {'property': PROPERTY, 'reportDate': report_date,
            'capturedAt': datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(),
            'provisional': target >= today - timedelta(days=1),
            'caveats': ['Property timezone is returned in report metadata; match receipt time to that timezone.',
                        'Event time is not email delivery time. Time matching alone does not identify a person.',
                        'Internal exclusion applies only after each browser opts out; historical internal traffic remains.',
                        'generate_lead requires verification of the form-side implementation.'], 'reports': {}}
        for name, body in bodies.items():
            result = run_report(body, auth.token, session=auth.session)
            if not args.status_only:
                output['reports'][name] = result
        if args.status_only:
            output = connection_status('ok', mode, report_date, completed=len(bodies))
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except Exception as error:
        print(json.dumps(connection_status('error', mode, report_date, error=exception_code(error)),
                         ensure_ascii=False, indent=2))
        return 1
    finally:
        if auth is not None and auth.session is not None:
            try:
                auth.session.close()
            except Exception:
                pass


if __name__ == '__main__':
    sys.exit(main())
