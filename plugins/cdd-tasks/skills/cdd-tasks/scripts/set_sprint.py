#!/usr/bin/env python3
"""Назначение спринта и плановых дат задачам Scrumban через GitHub CLI."""
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

OWNER = 'Cringe-Driven-Development-Team'


def normalize_issue_url(value: str) -> str:
    match = re.fullmatch(
        rf'https://github\.com/{OWNER}/([a-z0-9_.-]+)/issues/([1-9][0-9]*)/?',
        value, re.IGNORECASE,
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
