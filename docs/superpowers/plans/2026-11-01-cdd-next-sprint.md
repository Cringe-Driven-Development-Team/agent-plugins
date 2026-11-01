# CDD Next Sprint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Научить cdd-tasks распознавать Next Sprint, назначать следующую итерацию и проверять результат без изменения статуса.

**Architecture:** Дополняем существующие инструкции и справочник, используя поле Sprint и gh project item-edit. Добавляем один сценарий оценки по принятому в репозитории формату; новых скриптов и зависимостей нет.

**Tech Stack:** Markdown, GitHub GraphQL, gh, существующие Bash-проверки.

**Spec:** [2026-11-01-cdd-next-sprint-design.md](../specs/2026-11-01-cdd-next-sprint-design.md)

## Global Constraints

- Назначение следующего спринта сохраняет Status, если пользователь отдельно не поручил его изменить.
- ID проекта, полей и итераций читаются через API; не фиксируются в инструкции.
- Тестирование не изменяет GitHub; установленный кэш плагина вручную не правим.

## Review Focus

- Первый день новой итерации: предыдущая уже не текущая; конец интервала исключён.
- Несортированные итерации: следующая определяется по датам.
- Перерыв между итерациями: агент уточняет целевой спринт.
- Следующей итерации нет: агент сообщает об этом, не создаёт её.
- Ответ изменения успешен, но поле не сохранилось: агент проверяет iterationId и Status повторным чтением.

## Task 1: Инструкции и проверка назначения следующего спринта

**Files:**
- Modify: `plugins/cdd-tasks/skills/cdd-tasks/SKILL.md`
- Modify: `plugins/cdd-tasks/skills/cdd-tasks/REFERENCE.md`
- Create: `plugins/cdd-tasks/evals/next-sprint/prompt.md`
- Create: `plugins/cdd-tasks/evals/next-sprint/graders/criteria.md`
- Create: `plugins/cdd-tasks/evals/next-sprint/graders/skill.md`

**Interfaces:** Существующие поле Sprint, ProjectV2Item.fieldValueByName и gh project item-edit; новых интерфейсов нет.

- [ ] Составить сценарий разбора без сети и записей: назначение следующего спринта со статусом In review, граница дат, несортированные итерации, перерыв, отсутствие будущей итерации и несовпадение iterationId после записи. Включить вопрос о назначении представления Next Sprint и действующих фильтрах.
- [ ] Прогнать сценарий независимым агентом со старой инструкцией. Сохранить наблюдения baseline в журнале проверки; не придумывать провал, если агент справился. При отсутствии провала не добавлять неподтверждённые правила сверх согласованной справочной правки.
- [ ] Дополнить SKILL.md кратким правилом и ссылкой на REFERENCE §3; в справочнике описать Next Sprint, актуальные фильтры Backlog/Sprint, интервалы дат, выбор следующей итерации и повторное чтение Sprint/Status через API. Сохранить существующую команду назначения и ограничение на изменение полей только по просьбе.
- [ ] Повторить тот же сценарий независимым агентом с изменённой инструкцией. Проверить все пять условий Review Focus и соответствие исходным четырём пунктам пользователя.
- [ ] Выполнить `bash plugins/cdd-tasks/tests/check_docs.sh`, `bash tests/manifest_validation_test.sh`, `bash tests/manifest_test.sh`, `python3 /home/oleg/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/cdd-tasks/skills/cdd-tasks` и `git diff --check`. Ожидается exit 0; не добавлять проверки точных формулировок текста.
- [ ] Проверить итоговый diff, сохранить журнал baseline/после правки в `docs/superpowers/verification/2026-11-01-cdd-next-sprint.md` и закоммитить завершённую задачу.

Способ выполнения пользователь пока не выбрал. До выбора инструкция не меняется.
