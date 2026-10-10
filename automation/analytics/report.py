#!/usr/bin/env python3
"""Read-only GA4 follow-up. Prints request definitions unless --execute is supplied.

No credentials or report results are written to this public repository.
"""
import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

PROPERTY = '547125968'


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


def run_report(body, token, transport=urlopen):
    rows, metadata, offset = [], None, 0
    while True:
        request_body = dict(body, offset=str(offset))
        req = Request(f'https://analyticsdata.googleapis.com/v1beta/properties/{PROPERTY}:runReport',
            data=json.dumps(request_body).encode(), headers={
                'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}, method='POST')
        with transport(req, timeout=30) as response:
            result = json.load(response)
        page = result.get('rows', [])
        if metadata is None:
            metadata = {k: v for k, v in result.items() if k != 'rows'}
        rows.extend(page)
        count = int(result.get('rowCount', 0))
        if len(rows) >= count:
            return dict(metadata, rows=rows)
        if not page:
            raise RuntimeError('Pagination stopped before rowCount; result is incomplete.')
        offset += len(page)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date', help='Inquiry date, YYYY-MM-DD; default: 2 days ago in Japan')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    today = datetime.now(ZoneInfo('Asia/Tokyo')).date()
    target = date.fromisoformat(args.date) if args.date else today - timedelta(days=2)
    if target > today:
        parser.error('Future dates cannot be queried.')
    bodies = reports(target.isoformat(), target.isoformat())
    if not args.execute:
        print(json.dumps({'mode': 'request_preview', 'property': PROPERTY, 'reports': bodies}, ensure_ascii=False, indent=2))
        return
    token = os.environ.get('GA4_ACCESS_TOKEN')
    if not token:
        parser.error('GA4_ACCESS_TOKEN is required in the local environment; do not paste credentials into chat.')
    output = {'property': PROPERTY, 'reportDate': target.isoformat(),
        'capturedAt': datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(),
        'provisional': target >= today - timedelta(days=1),
        'caveats': ['Property timezone is returned in report metadata; match receipt time to that timezone.',
                    'Event time is not email delivery time. Time matching alone does not identify a person.',
                    'Internal exclusion applies only after each browser opts out; historical internal traffic remains.',
                    'generate_lead requires verification of the form-side implementation.'], 'reports': {}}
    try:
        for name, body in bodies.items():
            output['reports'][name] = run_report(body, token)
    except HTTPError as error:
        print(f'GA4 request failed (HTTP {error.code}); no result is reported as zero.', file=sys.stderr)
        sys.exit(1)
    except (OSError, ValueError, RuntimeError):
        print('GA4 request failed or returned incomplete data; retry after checking access.', file=sys.stderr)
        sys.exit(1)
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
