"""Планирование задач: тесты не обращаются к GitHub."""
import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfoNotFoundError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/cdd-tasks/scripts'))
import set_sprint as app


S8 = dict(id='s8', title='Sprint 8', startDate='2026-11-02', duration=7)
S9 = dict(id='s9', title='Sprint 9', startDate='2026-11-09', duration=7)
S10 = dict(id='s10', title='Sprint 10', startDate='2026-11-16', duration=7)
URL_A = 'https://github.com/Cringe-Driven-Development-Team/frontend/issues/6'


class DatesTest(unittest.TestCase):
    def test_inclusive_end_and_year_boundary(self):
        for iteration, expected in [
            (S10, ('2026-11-16', '2026-11-22')),
            ({**S10, 'startDate': '2026-12-28'}, ('2026-12-28', '2027-01-03')),
            ({**S10, 'duration': 1}, ('2026-11-16', '2026-11-16')),
        ]:
            with self.subTest(iteration=iteration):
                self.assertEqual(app.resolve_dates(iteration, None, None), expected)

    def test_explicit_dates_override_bounds(self):
        for start, end in [('2026-11-18', '2026-11-19'),
                           ('2026-11-15', '2026-11-23'),
                           ('2026-11-18', '2026-11-18')]:
            with self.subTest(start=start, end=end):
                self.assertEqual(app.resolve_dates(S10, start, end), (start, end))

    def test_rejects_invalid_date_pair(self):
        for start, end in [(None, '2026-11-19'), ('2026-11-18', None),
                           ('2026-02-30', '2026-11-19'), ('20261118', '2026-11-19'),
                           ('2026-1-8', '2026-11-19'), ('2026-11-20', '2026-11-19')]:
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                app.resolve_dates(S10, start, end)

    def test_rejects_invalid_iteration_fields(self):
        for change in [{'duration': 0}, {'duration': -1}, {'duration': '7'},
                       {'duration': True}, {'startDate': 'bad'}, {'startDate': None},
                       {'id': ''}, {'title': 9}, {'startDate': '9999-12-31'}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                app.select_iteration([{**S10, **change}], '@current', date(2026, 11, 16))


class IterationTest(unittest.TestCase):
    def test_selects_by_date_not_array_order(self):
        self.assertEqual(app.select_iteration([S10, S8, S9], '@next', date(2026, 11, 15)), S10)
        self.assertEqual(app.select_iteration([S10, S8, S9], '@current', date(2026, 11, 16)), S10)

    def test_explicit_name_can_select_completed_iteration(self):
        self.assertEqual(app.select_iteration([S10, S8, S9], 'Sprint 8', date(2026, 11, 15)), S8)

    def test_ambiguity_and_missing_iterations_are_errors(self):
        for iterations, selector, today in [
            ([{**S8, 'startDate': '2026-11-04'}, S9], '@next', date(2026, 11, 2)),
            ([S8], '@next', date(2026, 11, 2)),
            ([S9, {**S9, 'id': 'overlap'}], '@current', date(2026, 11, 15)),
            ([S9, S10, {**S10, 'id': 'tie'}], '@next', date(2026, 11, 15)),
            ([S10, {**S10, 'id': 'duplicate'}], 'Sprint 10', date(2026, 11, 15)),
            ([S10], 'Sprint 99', date(2026, 11, 15)),
        ]:
            with self.subTest(iterations=iterations, selector=selector), self.assertRaises(ValueError):
                app.select_iteration(iterations, selector, today)


class UrlTest(unittest.TestCase):
    def test_normalizes_case_and_trailing_slash(self):
        self.assertEqual(app.normalize_issue_url(URL_A + '/'), URL_A)
        self.assertEqual(app.normalize_issue_url(URL_A.upper()), URL_A)

    def test_rejects_non_issue_urls(self):
        for url in [URL_A + '?x=1', URL_A + '#comment', URL_A.replace('/issues/', '/pull/'),
                    URL_A.replace('github.com', 'example.com'), URL_A.replace('https:', 'http:'),
                    URL_A.replace('github.com', 'user@github.com'),
                    URL_A.replace('Cringe-Driven-Development-Team', 'Other'),
                    URL_A.replace('/6', '/0'), URL_A.replace('/6', '/-1'),
                    URL_A.replace('/frontend/', '/../'), '\n' + URL_A]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                app.normalize_issue_url(url)


class ClockTest(unittest.TestCase):
    def test_uses_moscow_date_at_utc_boundary(self):
        with mock.patch.object(app, 'datetime') as clock:
            instant = datetime(2026, 11, 15, 21, 30, tzinfo=timezone.utc)
            clock.now.side_effect = lambda tz: instant.astimezone(tz)
            self.assertEqual(app.moscow_today(), date(2026, 11, 16))

    def test_missing_timezone_is_explained(self):
        with mock.patch.object(app, 'ZoneInfo', side_effect=ZoneInfoNotFoundError('missing')):
            with self.assertRaisesRegex(ValueError, 'Europe/Moscow'):
                app.moscow_today()
