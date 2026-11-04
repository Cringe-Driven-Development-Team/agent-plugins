# cdd-apidog Rename Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Переименовать новый плагин и скилл в `cdd-apidog` в существующем PR #26.

**Architecture:** Механическое переименование одной поставки для Claude Code и Codex. Обновляются оба marketplace и существующие проверки; содержательная часть скилла сохраняется.

**Tech Stack:** Markdown, JSON, Bash, существующий Python-валидатор скиллов, GitHub CLI.

**Spec:** `docs/superpowers/specs/2026-11-04-cdd-apidog-rename-design.md`.

## Global Constraints

- Новые имена: `cdd-apidog`, `cdd-apidog@cdd`, `cdd-apidog:cdd-apidog`.
- Не менять другие плагины, поведение скилла, scope установки или API-инструкции.
- Не добавлять alias прежнего имени; не сливать PR и не устанавливать плагин.
- Использовать существующую ветку `skill/apidog-cdd` и worktree; сохранить имя ветки.
- Исторические проверки не переписывать как новые результаты.

## Review Focus

- Оба host-каталога и манифеста должны указывать на один новый каталог: existing manifest tests.
- Отрицательные сценарии должны проверять новое имя и путь: existing manifest validation tests.
- README и справочник ревью не должны предлагать старое имя: поиск по активным файлам.
- Относительная ссылка на `references/review.md` должна работать после переноса: проверить наличие файла и ссылку в SKILL.md.
- Старые записи проверки и имя ветки допустимы только как объяснённая история: просмотр diff документации.

### Task 1: Согласованное переименование и обновление PR

**Files:**
- Move: `plugins/apidog-cdd/` → `plugins/cdd-apidog/` и вложенный `skills/apidog-cdd/` → `skills/cdd-apidog/`.
- Modify: оба `plugin.json`, `SKILL.md`, `references/review.md` внутри нового каталога.
- Modify: `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `README.md`.
- Modify: `tests/manifest_test.sh`, `tests/manifest_validation_test.sh`.
- Annotate: прежние `docs/superpowers/{specs,plans,verification}/2026-11-04-apidog-cdd*.md` ссылкой на согласованное переименование.
- Create: `docs/superpowers/verification/2026-11-04-cdd-apidog-rename.md` с фактическими результатами новых проверок.

**Interfaces:** Consumes существующую поставку `apidog-cdd`; produces устанавливаемый `cdd-apidog@cdd` и скилл `cdd-apidog:cdd-apidog` с прежними инструкциями.

- [ ] Перенести каталоги и заменить старые имена в активных файлах. В тестах обновить также имена функций `test_missing_apidog_cdd_*` и их вызовы. `EXPECTED` остаётся отсортированным: ansible, cdd-apidog, cdd-tasks, frontend-packages, pulumi, selectel-ops.
- [ ] Обновить README: селектор, таблицу, ссылки и правило `cdd-<область>` для командного контекста. В прежних документах добавить примечания о новом имени, сохранив факты выполненных команд и коммитов.
- [ ] Выполнить `rg -n --hidden 'apidog-cdd|apidog_cdd' plugins/cdd-apidog README.md tests .claude-plugin .agents`. Ожидание: совпадений нет (exit 1). Проверить ссылку и наличие `plugins/cdd-apidog/skills/cdd-apidog/references/review.md`.
- [ ] Запустить `bash tests/manifest_test.sh` и `bash tests/manifest_validation_test.sh`. Ожидание: 6 плагинов / 12 скиллов, все существующие сценарии проходят.
- [ ] Запустить `python3 /home/oleg/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/cdd-apidog/skills/cdd-apidog`, `claude plugin validate plugins/cdd-apidog`, `git diff --check`. Ожидание: exit 0; известное предупреждение об отсутствии version допустимо по правилам репозитория.
- [ ] Просмотреть diff с обнаружением переименований; убедиться, что инструкции изменились только в именах. Записать результаты в новый verification-файл, отметить шаги плана и закоммитить переименование.
- [ ] Пройти ревью по выбранному способу исполнения; исправить замечания и повторить только затронутые проверки.
- [ ] Отправить ветку в origin. Обновить title/body PR #26 на новое имя, сохранив описание всего скилла; для body использовать временный файл и `--body-file`. Проверить PR head, заголовок и отсутствие активных ссылок на старое имя. Не выполнять merge/install.

Новые поведенческие тесты не нужны: проверяется переименование существующими проверками упаковки и валидаторами.

## Self-review

Спецификация покрыта одной задачей; перенос, документация и тесты составляют одну поставку. Проверки упаковки, ссылок, старых имён и исторических записей перечислены выше. Новых API, зависимостей и способов установки нет.
