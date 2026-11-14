#!/usr/bin/env python3
"""Назначение спринта и плановых дат задачам Scrumban через GitHub CLI."""
import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

OWNER = 'Cringe-Driven-Development-Team'


def normalize_issue_url(value: str) -> str:
    match = re.fullmatch(
        rf'https://github\.com/{OWNER}/([a-z0-9_.-]+)/issues/([1-9][0-9]*)/?',
        value, re.IGNORECASE | re.ASCII,
    )
    if not match or match[1] in ('.', '..'):
        raise ValueError(f'Нужна ссылка на issue организации {OWNER}: {value}')
    return f'https://github.com/{OWNER}/{match[1].lower()}/issues/{match[2]}'


def parse_date(value: str) -> date:
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
        raise ValueError(f'Нужна дата YYYY-MM-DD: {value}')
    return date.fromisoformat(value)


def iteration_bounds(iteration: dict) -> tuple:
    if any(not isinstance(iteration.get(key), str) or not iteration[key] for key in ('id', 'title')):
        raise ValueError('У итерации отсутствует id или название')
    duration = iteration.get('duration')
    if type(duration) is not int or duration <= 0:
        raise ValueError('Длительность итерации должна быть положительным числом дней')
    start = parse_date(iteration.get('startDate'))
    try:
        return start, start + timedelta(days=duration)
    except OverflowError as exc:
        raise ValueError('Дата окончания итерации вне допустимого диапазона') from exc


def select_iteration(iterations: list, selector: str, today: date) -> dict:
    bounds = [(item, *iteration_bounds(item)) for item in iterations]
    if selector in ('@current', '@next'):
        current = [(item, end) for item, start, end in bounds if start <= today < end]
        if len(current) != 1:
            raise ValueError('Нет однозначного текущего спринта; укажите его название')
        if selector == '@current':
            return current[0][0]
        future = [(item, start) for item, start, end in bounds if start >= current[0][1]]
        if not future:
            raise ValueError('Следующий спринт не задан')
        nearest = min(start for item, start in future)
        matches = [item for item, start in future if start == nearest]
    else:
        matches = [item for item, start, end in bounds if item['title'] == selector]
    if len(matches) != 1:
        raise ValueError(f'Нет однозначного спринта {selector}; уточните название')
    return matches[0]


def resolve_dates(iteration: dict, start, end) -> tuple:
    if (start is None) != (end is None):
        raise ValueError('--start и --end нужно задавать вместе')
    if start is not None:
        first, last = parse_date(start), parse_date(end)
    else:
        first, exclusive_end = iteration_bounds(iteration)
        last = exclusive_end - timedelta(days=1)
    if first > last:
        raise ValueError('Start Date не может быть позже End Date')
    return first.isoformat(), last.isoformat()


def moscow_today() -> date:
    try:
        return datetime.now(ZoneInfo('Europe/Moscow')).date()
    except ZoneInfoNotFoundError as exc:
        raise ValueError('Нет системных данных часового пояса Europe/Moscow') from exc


def gh_graphql(query: str, variables: dict) -> dict:
    try:
        result = subprocess.run(
            ['gh', 'api', 'graphql', '--input', '-'],
            input=json.dumps({'query': query, 'variables': variables}),
            text=True, capture_output=True, shell=False, timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f'Не удалось выполнить gh: {exc}') from exc
    if result.returncode:
        raise RuntimeError(f'Ошибка gh: {result.stderr or result.stdout}')
    try:
        response = json.loads(result.stdout)
    except ValueError as exc:
        raise RuntimeError(f'Ответ gh не является JSON: {result.stdout}') from exc
    if not isinstance(response, dict) or response.get('errors') or not isinstance(response.get('data'), dict):
        raise RuntimeError(f'Ошибка GraphQL: {json.dumps(response, ensure_ascii=False)}')
    return response['data']


def load_project() -> dict:
    query = '''query LoadProject($owner: String!, $after: String) {
      organization(login: $owner) { projectV2(number: 1) {
        id
        fields(first: 100) {
          pageInfo { hasNextPage endCursor }
          nodes {
            ... on ProjectV2Field { id name dataType }
            ... on ProjectV2SingleSelectField { id name dataType }
            ... on ProjectV2IterationField {
              id name dataType
              configuration {
                iterations { id title startDate duration }
                completedIterations { id title startDate duration }
              }
            }
          }
        }
        items(first: 100, after: $after) {
          pageInfo { hasNextPage endCursor }
          nodes { id isArchived content { __typename ... on Issue { url } } }
        }
      } }
    }'''
    items, cursors = [], set()
    after = None
    while True:
        project = gh_graphql(query, {'owner': OWNER, 'after': after})['organization']['projectV2']
        if not project:
            raise RuntimeError('Scrumban №1 недоступен')
        if project['fields']['pageInfo']['hasNextPage']:
            raise RuntimeError('Список полей усечён; запись отменена')
        items.extend(project['items']['nodes'])
        page = project['items']['pageInfo']
        if not page['hasNextPage']:
            return {'id': project['id'], 'fields': project['fields']['nodes'], 'items': items}
        after = page['endCursor']
        if not after or after in cursors:
            raise RuntimeError('Невозможно прочитать следующую страницу карточек')
        cursors.add(after)


def read_item(item_id: str) -> dict:
    query = '''query ReadItem($item: ID!) {
      node(id: $item) { ... on ProjectV2Item {
        sprint: fieldValueByName(name: "Sprint") {
          ... on ProjectV2ItemFieldIterationValue { iterationId }
        }
        start: fieldValueByName(name: "Start Date") {
          ... on ProjectV2ItemFieldDateValue { date }
        }
        end: fieldValueByName(name: "End Date") {
          ... on ProjectV2ItemFieldDateValue { date }
        }
        status: fieldValueByName(name: "Status") {
          ... on ProjectV2ItemFieldSingleSelectValue { optionId }
        }
      } }
    }'''
    state = gh_graphql(query, {'item': item_id})['node']
    if not isinstance(state, dict):
        raise RuntimeError(f'Карточка {item_id} недоступна')
    for field, key in [('sprint', 'iterationId'), ('start', 'date'), ('end', 'date'), ('status', 'optionId')]:
        if field not in state or (state[field] is not None and
                                 (not isinstance(state[field], dict) or not state[field].get(key))):
            raise RuntimeError(f'Не удалось прочитать поле {field} карточки {item_id}')
    return state


def write_schedule(project_id: str, item_id: str, fields: dict, iteration_id: str, start: str, end: str) -> None:
    query = '''mutation SetSchedule(
      $sprint: UpdateProjectV2ItemFieldValueInput!,
      $start: UpdateProjectV2ItemFieldValueInput!,
      $end: UpdateProjectV2ItemFieldValueInput!
    ) {
      sprint: updateProjectV2ItemFieldValue(input: $sprint) { projectV2Item { id } }
      start: updateProjectV2ItemFieldValue(input: $start) { projectV2Item { id } }
      end: updateProjectV2ItemFieldValue(input: $end) { projectV2Item { id } }
    }'''
    variables = {}
    for alias, name, value in [('sprint', 'Sprint', {'iterationId': iteration_id}),
                               ('start', 'Start Date', {'date': start}),
                               ('end', 'End Date', {'date': end})]:
        variables[alias] = dict(projectId=project_id, itemId=item_id, fieldId=fields[name]['id'], value=value)
    result = gh_graphql(query, variables)
    if any(((result.get(key) or {}).get('projectV2Item') or {}).get('id') != item_id for key in variables):
        raise RuntimeError('GitHub не подтвердил запись всех трёх полей')


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('issues', nargs='+', help='Ссылки на issues организации CDD')
    parser.add_argument('--sprint', required=True, help='Название спринта, @current или @next')
    parser.add_argument('--start', help='Явное начало YYYY-MM-DD; только вместе с --end')
    parser.add_argument('--end', help='Явный конец YYYY-MM-DD включительно')
    args = parser.parse_args(argv)
    try:
        urls = list(dict.fromkeys(normalize_issue_url(url) for url in args.issues))
        if args.start is not None or args.end is not None:
            resolve_dates({}, args.start, args.end)
    except ValueError as exc:
        print(f'Ошибка аргументов: {exc}', file=sys.stderr)
        return 2

    try:
        project = load_project()
        fields = {}
        for name, kind in [('Sprint', 'ITERATION'), ('Start Date', 'DATE'), ('End Date', 'DATE')]:
            matches = [f for f in project['fields'] if f.get('name') == name]
            if len(matches) != 1 or matches[0].get('dataType') != kind or not matches[0].get('id'):
                raise ValueError(f'Нужно одно поле {name} типа {kind}')
            fields[name] = matches[0]
        config = fields['Sprint']['configuration']
        today = moscow_today() if args.sprint in ('@current', '@next') else None
        iteration = select_iteration(config['iterations'] + config['completedIterations'], args.sprint, today)
        start, end = resolve_dates(iteration, args.start, args.end)
        targets = []
        for url in urls:
            matches = [item for item in project['items'] if item.get('content') and
                       item['content'].get('__typename') == 'Issue' and
                       item['content']['url'].rstrip('/').lower() == url.lower()]
            if len(matches) != 1 or matches[0]['isArchived']:
                raise ValueError(f'Нужна одна неархивированная карточка в Scrumban: {url}')
            targets.append((url, matches[0]['id']))
    except (RuntimeError, ValueError, KeyError, TypeError) as exc:
        print(f'Запись не начата: {exc}', file=sys.stderr)
        return 1

    completed = []
    for index, (url, item_id) in enumerate(targets):
        before, after, error = None, None, None
        try:
            before = read_item(item_id)
        except (RuntimeError, KeyError, TypeError) as exc:
            error = f'Не прочитаны исходные значения, запись не начата: {exc}'
        if error is None:
            try:
                write_schedule(project['id'], item_id, fields, iteration['id'], start, end)
            except (RuntimeError, KeyError, TypeError) as exc:
                error = str(exc)
            # Даже при ошибке записи GitHub мог успеть изменить часть полей.
            try:
                after = read_item(item_id)
            except (RuntimeError, KeyError, TypeError) as exc:
                error = f'{error or ""} Результат неизвестен: {exc}'
            if after is not None:
                expected = dict(sprint={'iterationId': iteration['id']}, start={'date': start},
                                end={'date': end}, status=before['status'])
                if after != expected:
                    error = f'{error or ""} Значения после записи не совпали с ожидаемыми'
        if error:
            print(f'Ошибка для {url}: {error}', file=sys.stderr)
            print('До записи: ' + json.dumps(before, ensure_ascii=False), file=sys.stderr)
            print('После: ' + (json.dumps(after, ensure_ascii=False) if after is not None else 'неизвестно'), file=sys.stderr)
            print('Подтверждены: ' + (', '.join(completed) or 'нет'), file=sys.stderr)
            print('Не обработаны: ' + (', '.join(u for u, _ in targets[index + 1:]) or 'нет'), file=sys.stderr)
            return 1
        completed.append(url)
        print(f'OK {url}: {iteration["title"]}, {start} — {end}; Status сохранён')
    return 0


if __name__ == '__main__':
    sys.exit(main())
