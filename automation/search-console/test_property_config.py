import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('monitor', Path(__file__).with_name('search_console_automation.py'))
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


class PropertyConfigTest(unittest.TestCase):
    def test_restored_state_cannot_override_config(self):
        state = {'siteUrl': 'https://framepact.jp/', 'sitemapUrl': 'https://old.example/sitemap.xml',
                 'pages': [{'errorInfo': 'HTTPError:HTTP 403', 'retryAfter': '2099-01-01T00:00:00+09:00', 'consecutiveApiFailures': 3},
                           {'errorInfo': 'HTTPError:HTTP 500', 'retryAfter': '2099-01-01T00:00:00+09:00'}]}
        config = {'siteUrl': 'sc-domain:framepact.jp', 'sitemapUrl': 'https://framepact.jp/sitemap.xml'}
        with patch.object(monitor, 'load', side_effect=[copy.deepcopy(state), config]):
            result = monitor.load_register()
        self.assertEqual(result['siteUrl'], config['siteUrl'])
        self.assertEqual(result['sitemapUrl'], config['sitemapUrl'])
        self.assertIsNone(result['pages'][0]['retryAfter'])
        self.assertEqual(result['pages'][0]['consecutiveApiFailures'], 3)
        self.assertEqual(result['pages'][0]['errorInfo'], 'HTTPError:HTTP 403')
        self.assertEqual(result['pages'][1], state['pages'][1])
        result['pages'][0]['retryAfter'] = '2099-01-01T00:00:00+09:00'
        with patch.object(monitor, 'load', side_effect=[copy.deepcopy(result), config]):
            self.assertEqual(monitor.load_register(), result)


if __name__ == '__main__':
    unittest.main()
