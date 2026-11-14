# cdd-tasks

Скилл для работы с задачами и PR команды из Claude Code: в каком репозитории заводить задачу,
как её назвать и описать, как разбить на sub-issues работу, которая затрагивает несколько
репозиториев, как выставить статус, спринт и даты Gantt на доске, что писать в описании PR — `Closes` или
`Part of`. После merge — как проверить CI и учебную копию, повторить sync без
deploy и понять Telegram-уведомления.

Сами правила — в [CONTRIBUTING.md](https://github.com/Cringe-Driven-Development-Team/.github/blob/main/CONTRIBUTING.md)
организации. Скилл их не заменяет: он читает их перед работой и добавляет то, что нужно агенту, —
карту репозиториев и точные команды `gh`.

## Требования

- `gh`, авторизованный в GitHub с доступом к организации.
- Для статуса и спринта на доске — scope `project`: `gh auth refresh -s project`.
- Для скрипта назначения спринта — Python 3.9+ без дополнительных пакетов.
  Для относительных спринтов нужны системные данные `Europe/Moscow`; при их
  отсутствии скрипт сообщает ошибку до записи, не подставляя локальный часовой пояс.

## Спринт и даты Gantt

Поручение «поставь/перенеси в спринт» выставляет `Sprint`, `Start Date`, `End Date`:
обе даты по границам спринта, включая последний день. Старые даты перезаписываются;
явно запрошенные начало и конец имеют приоритет. Если названа только одна дата,
агент уточняет вторую. Статус сохраняется.

Из каталога плагина:

```bash
python3 skills/cdd-tasks/scripts/set_sprint.py \
  https://github.com/Cringe-Driven-Development-Team/frontend/issues/6 --sprint @next
```

Скрипт принимает ссылки на задачи и спринт (`Sprint N`, `@current`, `@next`),
при необходимости — `--start YYYY-MM-DD --end YYYY-MM-DD`. Детали, несколько задач
за один вызов и настройка Gantt — [REFERENCE §3](skills/cdd-tasks/REFERENCE.md#3-доска).
Код 0 означает проверенное сохранение всех задач; при частичном сбое скрипт
останавливается и сообщает фактическое либо неизвестное состояние.

Ручная смена Sprint в интерфейсе GitHub даты автоматически не меняет.

## Подключение

В `.claude/settings.json` репозитория:

```json
{
  "extraKnownMarketplaces": {
    "cdd": { "source": { "source": "github", "repo": "Cringe-Driven-Development-Team/agent-plugins" } }
  },
  "enabledPlugins": {
    "cdd-tasks@cdd": true
  }
}
```

## Чего скилл не делает

- Не вливает PR в обход обязательного ревью.
- Без просьбы не переводит задачи в спринт, не меняет исполнителя и не правит чужие описания:
  такие изменения уходят уведомлением в чат команды.
- Не проверяет доску: задачи без описания и PR без привязки он не ищет.

## Проверка

Из корня маркетплейса:

```bash
bash plugins/cdd-tasks/tests/check_docs.sh
python3 -m unittest discover -s plugins/cdd-tasks/tests -p 'test_set_sprint.py' -v
claude plugin eval plugins/cdd-tasks --case multi-repo-task --runs 3
claude plugin eval plugins/cdd-tasks --case post-merge-sync --runs 3
claude plugin eval plugins/cdd-tasks --case next-sprint --runs 3
```

Unittest подставляет ответы GitHub и не пишет на доску. Команды `claude plugin eval`
вызывают модель, запускаются отдельно вручную и могут быть платными.
