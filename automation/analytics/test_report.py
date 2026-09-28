import io
import json
import unittest
from report import reports, run_report


class ReportTests(unittest.TestCase):
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
            return io.StringIO(json.dumps({'rowCount': 2, 'rows': [{'value': body['offset']}],
                                          'metadata': {'timeZone': 'Asia/Tokyo'}}))
        result = run_report({}, 'test-only', transport)
        self.assertEqual(calls, ['0', '1'])
        self.assertEqual(len(result['rows']), 2)
        self.assertEqual(result['metadata']['timeZone'], 'Asia/Tokyo')

    def test_incomplete_response_is_not_reported_as_success(self):
        def transport(req, timeout):
            return io.StringIO('{"rowCount":1,"rows":[]}')
        with self.assertRaises(RuntimeError):
            run_report({}, 'test-only', transport)


if __name__ == '__main__':
    unittest.main()
