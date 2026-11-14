# cdd-tasks

Скилл для работы с задачами и PR команды из Claude Code и Codex: в каком репозитории заводить задачу,
как её назвать и описать, как разбить на sub-issues работу, которая затрагивает несколько
репозиториев, как выставить статус, спринт и даты Gantt на доске, что писать в описании PR — `Closes` или
`Part of`. Вместе с `docs-modules` добавляет треки в граф и связывает задачи полем
«Трек», учитывая наследование и спринты, сохраняя остальные поля.

Frontend после merge остаётся открытым в `Ready for build`, после публикации
Release — в `Ready for release`. Штатно CD закрывает задачу как completed/Done
после Health check и сохранённого production success. Backend и остальные
репозитории сохраняют закрытие при merge. Скилл учитывает ручные closed/reopen
и rollback, разделяет CI, sync, Release и production. Course-sync восстанавливается
отдельно без deploy; сбой обновления frontend issues — через `reconcile-issues.yml`
с проверенным исходным Deployment ID, без повторной выкатки.

Сами правила — в [CONTRIBUTING.md](https://github.com/Cringe-Driven-Development-Team/.github/blob/main/CONTRIBUTING.md)
организации. Скилл их не заменяет: он читает их перед работой и добавляет то, что нужно агенту, —
карту репозиториев и точные команды `gh`. Явные инструкции владельца и действующие
разрешения сессии имеют приоритет над скиллом; личные исключения не меняют
общекомандную политику.

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

- Не инициирует merge из-за наличия прав. При поручении влить и действующем разрешении
  владельца на bypass review не просит апрув повторно: проверяет актуальный head,
  обязательный CI и конфликты, закрепляет SHA в merge, проверяет результат.
  Не меняет rulesets и не обходит проваленные/незавершённые checks.
- Без просьбы не переводит задачи в спринт, не меняет исполнителя и не правит чужие описания:
  такие изменения уходят уведомлением в чат команды.
- Не проверяет доску: задачи без описания и PR без привязки он не ищет.
- Просьба добавить трек разрешает соответствующие привязки, но не merge docs PR.
  Новые варианты «Трека» ждут штатного CI docs на main; локальный board sync не запускается.

## Проверка

Из корня маркетплейса:

```bash
bash plugins/cdd-tasks/tests/check_docs.sh
python3 -m unittest discover -s plugins/cdd-tasks/tests -p 'test_set_sprint.py' -v
claude plugin eval plugins/cdd-tasks --case multi-repo-task --runs 3
claude plugin eval plugins/cdd-tasks --case next-sprint --runs 3
claude plugin eval plugins/cdd-tasks --case post-merge-sync --runs 3
claude plugin eval plugins/cdd-tasks --case merge-authorization --runs 3
claude plugin eval plugins/cdd-tasks --case module-track --runs 3
```

`check_docs.sh` проверяет структуру, а evals — решения агента. Prompts ограничены
чтением: реальные merge, записи доски и recovery при проверке не выполняются.
Результаты актуализации и ограничения runner — в
[отчёте](../../docs/superpowers/verification/2026-11-15-cdd-tasks-refresh.md).

Unittest подставляет ответы GitHub и не пишет на доску. Команды `claude plugin eval`
вызывают модель, запускаются отдельно вручную и могут быть платными.
