"""Планирование задач: тесты не обращаются к GitHub."""
import copy
import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
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


URL_B = 'https://github.com/Cringe-Driven-Development-Team/backend/issues/7'
URL_C = 'https://github.com/Cringe-Driven-Development-Team/infra/issues/8'


class FakeGitHub:
    """Состояние внешнего Projects API; весь код CLI остаётся настоящим."""
    def __init__(self):
        self.fields = [
            dict(id='field-sprint', name='Sprint', dataType='ITERATION',
                 configuration=dict(iterations=[S10, S9], completedIterations=[S8])),
            dict(id='field-start', name='Start Date', dataType='DATE'),
            dict(id='field-end', name='End Date', dataType='DATE'),
            dict(id='field-status', name='Status', dataType='SINGLE_SELECT'),
        ]
        self.items = [dict(id=item_id, isArchived=False,
                           content=dict(__typename='Issue', url=url))
                      for item_id, url in [('a', URL_A), ('b', URL_B), ('c', URL_C)]]
        self.state = {item['id']: dict(sprint=dict(iterationId='s9'),
                                     start=dict(date='2026-11-12'), end=dict(date='2026-11-13'),
                                     status=dict(optionId='review')) for item in self.items}
        self.writes = []
        self.reads = []
        self.pages = []
        self.fail_item = None
        self.fail_readback = False
        self.mismatch = None
        self.truncated_fields = False

    def __call__(self, query, variables):
        if 'query LoadProject' in query:
            after = variables.get('after')
            self.pages.append(after)
            nodes = self.items[:1] if after is None else self.items[1:]
            return dict(organization=dict(projectV2=dict(
                id='project', fields=dict(nodes=copy.deepcopy(self.fields),
                                         pageInfo=dict(hasNextPage=self.truncated_fields, endCursor=None)),
                items=dict(nodes=copy.deepcopy(nodes),
                           pageInfo=dict(hasNextPage=after is None, endCursor='page2' if after is None else None)),
            )))
        if 'query ReadItem' in query:
            item_id = variables['item']
            self.reads.append(item_id)
            if self.fail_readback and any(w['itemId'] == item_id for w in self.writes):
                raise RuntimeError('read timed out')
            return dict(node=copy.deepcopy(self.state[item_id]))
        if 'mutation SetSchedule' in query:
            inputs = [variables[k] for k in ('sprint', 'start', 'end')]
            aliases = ['sprint', 'start', 'end']
            for alias, update in zip(aliases, inputs):
                if update['projectId'] != 'project':
                    raise AssertionError('wrong project')
                field = {'field-sprint': 'sprint', 'field-start': 'start', 'field-end': 'end'}[update['fieldId']]
                self.writes.append(copy.deepcopy(update))
                self.state[update['itemId']][field] = copy.deepcopy(update['value'])
                if update['itemId'] == self.fail_item:
                    raise RuntimeError('partial write or timeout')
            if self.mismatch:
                key, value = self.mismatch
                self.state[inputs[0]['itemId']][key] = value
            return {alias: dict(projectV2Item=dict(id=update['itemId']))
                    for alias, update in zip(aliases, inputs)}
        raise AssertionError('Unexpected GraphQL operation: ' + query)


class CliTest(unittest.TestCase):
    def setUp(self):
        self.api = FakeGitHub()

    def run_cli(self, args):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(app, 'gh_graphql', self.api, create=True), \
                mock.patch.object(app, 'moscow_today', return_value=date(2026, 11, 15)), \
                redirect_stdout(out), redirect_stderr(err):
            code = app.main(args)
        return code, out.getvalue() + err.getvalue()

    def test_assigns_three_fields_and_reads_back(self):
        code, text = self.run_cli([URL_A, '--sprint', 'Sprint 10'])
        self.assertEqual(code, 0, text)
        self.assertEqual(self.api.state['a'], dict(sprint=dict(iterationId='s10'),
                         start=dict(date='2026-11-16'), end=dict(date='2026-11-22'),
                         status=dict(optionId='review')))
        self.assertEqual(len(self.api.writes), 3)
        self.assertEqual(self.api.reads, ['a', 'a'])
        self.assertIn(URL_A, text)

    def test_explicit_dates_and_relative_sprint(self):
        code, text = self.run_cli([URL_A, '--sprint', '@next', '--start', '2026-11-18', '--end', '2026-11-19'])
        self.assertEqual(code, 0, text)
        self.assertEqual(self.api.state['a']['sprint'], dict(iterationId='s10'))
        self.assertEqual(self.api.state['a']['start'], dict(date='2026-11-18'))
        self.assertEqual(self.api.state['a']['end'], dict(date='2026-11-19'))

    def test_all_pages_and_duplicate_urls(self):
        code, text = self.run_cli([URL_B, URL_B + '/', '--sprint', 'Sprint 10'])
        self.assertEqual(code, 0, text)
        self.assertEqual(self.api.pages, [None, 'page2'])
        self.assertEqual([w['itemId'] for w in self.api.writes], ['b', 'b', 'b'])

    def test_unrelated_foreign_issue_does_not_block_requested_task(self):
        self.api.items.append(dict(id='foreign', isArchived=False,
                              content=dict(__typename='Issue', url='https://github.com/another/repo/issues/1')))
        code, text = self.run_cli([URL_A, '--sprint', 'Sprint 10'])
        self.assertEqual(code, 0, text)

    def test_null_mutation_result_is_read_back(self):
        api = self.api

        def null_result(query, variables):
            data = api(query, variables)
            if 'mutation SetSchedule' in query:
                data['end'] = {'projectV2Item': None}
            return data

        with mock.patch.object(app, 'gh_graphql', side_effect=null_result), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(app.main([URL_A, URL_B, '--sprint', 'Sprint 10']), 1)
        self.assertEqual(api.reads, ['a', 'a'])
        self.assertEqual(len(api.writes), 3)

    def test_invalid_last_target_prevents_all_writes(self):
        for problem in ['missing', 'archived', 'duplicate', 'wrong_type', 'missing_field', 'truncated_fields']:
            with self.subTest(problem=problem):
                self.api = FakeGitHub()
                if problem == 'missing': self.api.items.pop(1)
                if problem == 'archived': self.api.items[1]['isArchived'] = True
                if problem == 'duplicate': self.api.items.append(copy.deepcopy(self.api.items[1]))
                if problem == 'wrong_type': self.api.fields[1]['dataType'] = 'TEXT'
                if problem == 'missing_field': self.api.fields.pop(2)
                if problem == 'truncated_fields': self.api.truncated_fields = True
                code, text = self.run_cli([URL_A, URL_B, '--sprint', 'Sprint 10'])
                self.assertEqual(code, 1, text)
                self.assertEqual(self.api.writes, [])

    def test_empty_status_is_preserved(self):
        self.api.state['a']['status'] = None
        code, text = self.run_cli([URL_A, '--sprint', 'Sprint 10'])
        self.assertEqual(code, 0, text)
        self.assertIsNone(self.api.state['a']['status'])

    def test_readback_mismatch_stops_batch(self):
        for field, value in [('sprint', dict(iterationId='s9')), ('start', None),
                             ('end', dict(date='2026-11-21')), ('status', dict(optionId='ready'))]:
            with self.subTest(field=field):
                self.api = FakeGitHub()
                self.api.mismatch = field, value
                code, text = self.run_cli([URL_A, URL_B, '--sprint', 'Sprint 10'])
                self.assertEqual(code, 1, text)
                self.assertEqual([w['itemId'] for w in self.api.writes], ['a', 'a', 'a'])
                self.assertIn(URL_B, text)
                self.assertEqual(self.api.state['a'][field], value)

    def test_partial_graphql_error_is_read_back(self):
        self.api.fail_item = 'a'
        code, text = self.run_cli([URL_A, URL_B, '--sprint', 'Sprint 10'])
        self.assertEqual(code, 1, text)
        self.assertEqual(self.api.reads, ['a', 'a'])
        self.assertEqual(len(self.api.writes), 1)
        self.assertIn('2026-11-12', text)
        self.assertIn('partial write', text)
        self.assertIn(URL_B, text)

    def test_timeout_and_unreadable_result(self):
        self.api.fail_item = 'a'
        self.api.fail_readback = True
        code, text = self.run_cli([URL_A, URL_B, '--sprint', 'Sprint 10'])
        self.assertEqual(code, 1, text)
        self.assertEqual(len(self.api.writes), 1)
        self.assertEqual(self.api.reads, ['a', 'a'])
        self.assertIn('неизвест', text.lower())
        self.assertIn('read timed out', text)

    def test_failure_after_one_success(self):
        self.api.fail_item = 'b'
        code, text = self.run_cli([URL_A, URL_B, URL_C, '--sprint', 'Sprint 10'])
        self.assertEqual(code, 1, text)
        self.assertEqual([w['itemId'] for w in self.api.writes], ['a', 'a', 'a', 'b'])
        for url in [URL_A, URL_B, URL_C]: self.assertIn(url, text)
        self.assertEqual(self.api.state['a']['end'], dict(date='2026-11-22'))
        self.assertEqual(self.api.state['c']['sprint'], dict(iterationId='s9'))

    def test_invalid_arguments_before_mutations(self):
        for args in [[URL_A, '--sprint', 'Sprint 10', '--start', '2026-11-18'],
                     [URL_A + '?bad', '--sprint', 'Sprint 10'],
                     [URL_A, '--sprint', 'Sprint 10', '--start', '2026-11-19', '--end', '2026-11-18']]:
            with self.subTest(args=args):
                code, text = self.run_cli(args)
                self.assertEqual(code, 2, text)
                self.assertEqual(self.api.writes, [])

    def test_no_timezone_database(self):
        with mock.patch.object(app, 'ZoneInfo', side_effect=ZoneInfoNotFoundError('missing')), \
                mock.patch.object(app, 'gh_graphql', self.api, create=True), \
                redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
            self.assertEqual(app.main([URL_A, '--sprint', '@next']), 1)
        self.assertEqual(self.api.writes, [])

    def test_help_never_contacts_github(self):
        with mock.patch.object(app, 'gh_graphql', side_effect=AssertionError('network'), create=True), \
                redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as result:
            app.main(['--help'])
        self.assertEqual(result.exception.code, 0)


class TransportTest(unittest.TestCase):
    def test_uses_json_stdin_and_no_shell(self):
        result = subprocess.CompletedProcess([], 0, '{"data":{"ok":true}}', '')
        with mock.patch.object(subprocess, 'run', return_value=result) as run:
            self.assertEqual(app.gh_graphql('query Test{viewer{login}}', {'str': '$(bad)'}), {'ok': True})
        args, kwargs = run.call_args
        self.assertEqual(args[0], ['gh', 'api', 'graphql', '--input', '-'])
        self.assertFalse(kwargs.get('shell', False))
        self.assertEqual(kwargs['timeout'], 60)
        self.assertEqual(json.loads(kwargs['input'])['variables'], {'str': '$(bad)'})

    def test_rejects_transport_and_graphql_errors(self):
        for result in [subprocess.CompletedProcess([], 1, '', 'denied'),
                       subprocess.CompletedProcess([], 0, 'not json', ''),
                       subprocess.CompletedProcess([], 0, '{"data":{},"errors":[{"message":"partial"}]}', ''),
                       subprocess.CompletedProcess([], 0, '{"data":null}', '')]:
            with self.subTest(result=result), mock.patch.object(subprocess, 'run', return_value=result):
                with self.assertRaises(RuntimeError): app.gh_graphql('query', {})
        for error in [FileNotFoundError('gh'), subprocess.TimeoutExpired('gh', 60)]:
            with self.subTest(error=error), mock.patch.object(subprocess, 'run', side_effect=error):
                with self.assertRaises(RuntimeError): app.gh_graphql('mutation', {})
