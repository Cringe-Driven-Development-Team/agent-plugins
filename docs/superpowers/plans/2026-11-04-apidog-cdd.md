# Apidog CDD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить один командный скилл apidog-cdd с контекстом проекта и практикой ревью MR поверх официальных скиллов Apidog.

**Architecture:** Плагин `apidog-cdd@cdd` в существующем marketplace. Короткий SKILL.md содержит контекст и маршрутизацию; references/review.md загружается для ревью. Официальные скиллы устанавливаются отдельно, не копируются в репозиторий.

**Tech Stack:** Markdown, JSON manifests, существующие Bash/jq проверки; Apidog CLI/MCP только для read-only верификации.

**Spec:** `docs/superpowers/specs/2026-11-04-apidog-cdd-design.md` (согласована пользователем).

## Global Constraints

- Только `apidog-cdd`; не создавать apidog-ops, новый MCP или CLI wrapper.
- Поддержка Claude Code и Codex по структуре текущего репозитория; без фиксированной version.
- Проект `1382426`, команда `832765`; main `1388508` перепроверить перед фиксацией.
- Опубликованный контракт https://vb78fyael1.apidog.io/ обязательно включить в карту ссылок.
- Изменение участников и прав не входит в начальный объём. Не сохранять секреты или текущий список участников в скилле.
- Не дублировать официальные скиллы; загружать только нужный маршрут. При отсутствии официального скилла давать команду установки, не блокируя доступное чтение CLI.
- Не вводить legacy/безостановочный деплой. Учитывать уже данное поручение пользователя без повторного запроса разрешения.
- До выбора способа выполнения плана реализацию не начинать.

## Review Focus

1. Неполный MR/preview: не выдавать кандидатов и diff всех веток за состав MR (Task 2, сценарий B).
2. Устаревшая документация или MCP другой ветки: источник и ветка должны быть явными (Task 1, A; Task 2, B).
3. Только собственная роль: не объявлять её полным аудитом участников (Task 1, C).
4. Настройки с Cloud Mock token: фильтровать ответ до вывода, не сохранять секреты (Task 1, D).
5. Native-изменения и публикация: OpenAPI не покрывает все моки, review не разрешает approve/отправку сообщений (Task 2, E).

## Task 1: Контекст проекта и установка в обоих hosts

**Files:**
- Create: `plugins/apidog-cdd/skills/apidog-cdd/SKILL.md`
- Create: `plugins/apidog-cdd/.claude-plugin/plugin.json`
- Create: `plugins/apidog-cdd/.codex-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `README.md`
- Modify/test: `tests/manifest_test.sh`, `tests/manifest_validation_test.sh`
- Create: `docs/superpowers/verification/2026-11-04-apidog-cdd.md` (доказательства проверки, без секретов)

**Interfaces:** Consumes официальные скиллы из host catalog, текущий CLI help и ссылки утверждённой спеки. Produces устанавливаемый `apidog-cdd@cdd` / `apidog-cdd:apidog-cdd`; путь к справочнику ревью добавляется в Task 2.

- [x] Прочитать spec, AGENTS.md и актуальные main `backend/docs/apidog.md`, `frontend/docs/api-contract.md`, `.github/CONTRIBUTING.md`; сверить project/team/branch через существующую авторизацию, выводя только нужные поля. Зафиксировать источники и дату в verification.
- [x] Запустить базовые `bash tests/manifest_validation_test.sh` и `bash tests/manifest_test.sh`; сохранить результаты до изменений.
- [x] Обновить контракт инвентаря в manifest_test: добавить apidog-cdd в EXPECTED и цикл. В независимые fixture-списки manifest_validation добавить плагин; ожидаемые итоги: 6 плагинов/12 скиллов, с дополнительным динамическим скиллом — 13. Добавить случаи отсутствия регистрации apidog-cdd и его Codex manifest, ожидающие ненулевой exit и диагностику проблемного пути/набора. Запустить проверки: реальный marketplace должен не пройти до регистрации нового плагина.
- [x] Добавить оба манифеста по примеру frontend-packages (name `apidog-cdd`, author `Cringe-Driven-Development-Team`, Codex skills `./skills/`, без version) и обе регистрации по стилю соседних записей.
- [x] Написать SKILL.md: ссылки из spec, границы main/рабочей ветки/Cloud Mock, связь с источниками генерации и правилами команды. Для реальных команд отсылать к текущему help и официальным скиллам. Описать чтение проекта/прав с границами team get и фильтрацией настроек. Не зашивать абсолютные пути установки и меняющиеся MCP suffixes.
- [x] Обновить README: каталог, селектор apidog-cdd@cdd, актуальное количество плагинов/скиллов и установка официальных Apidog skills для обоих hosts через `npx -y skills add https://apidog.com --agent <codex|claude-code> --skill '*' --global --yes`. Пояснить отличие global от project scope, не запускать установку автоматически.
- [x] Проверить `bash tests/manifest_validation_test.sh`, `bash tests/manifest_test.sh` (6/12), `python3 /home/oleg/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/apidog-cdd/skills/apidog-cdd`, `git diff --check`. Все должны пройти.
- [x] Проверить сценарии на материалах скилла: A — запрос актуального main и разработка по sprint не смешивают ветки контракта/мока; C — запрос всех участников при наличии только teamPermissions завершается честной границей; D — ответ settings с token не попадает в вывод целиком. Записать наблюдаемое поведение в verification; не заменять проверки поиском буквальных фраз.
- [x] Коммит: `feat(apidog-cdd): add project context and dual-host packaging`.

## Task 2: Ревью MR и итоговая проверка

**Files:**
- Create: `plugins/apidog-cdd/skills/apidog-cdd/references/review.md`
- Modify: `plugins/apidog-cdd/skills/apidog-cdd/SKILL.md`
- Update: `docs/superpowers/verification/2026-11-04-apidog-cdd.md`

**Interfaces:** Consumes контекст/ссылки Task 1 и доступные CLI/MCP schemas. Produces маршрут ревью по ссылке из SKILL.md; никаких исполняемых helpers или новых внешних инструментов.

- [x] Описать весь порядок ревью из spec: MR selected resources, обе ветки/refs, preview partial и unsupported fields, native-ресурсы, схема/примеры/семантика, актуальная задача и потребители, откаты изменений target, формат доказуемого замечания и границы публикации.
- [x] Разделить проверенные возможности CLI и MCP: refresh OpenAPI не означает чтение ветки MR; preview — не field-level diff. Для неизвестной привязки/неполного scope нельзя выдавать полное ревью. Добавить ссылку на reference в SKILL.md только для review-запросов.
- [x] Сценарий B: read-only MR с выбранным подмножеством ресурсов, чужим изменением вне scope и partial preview. Ожидание: замечания ограничены выбранным scope, связанные схемы прочитаны, ограничения явно названы. Использовать сохранённые артефакты MR #40254 при наличии, а живые данные — только с новой датой; старые выводы не выдавать за свежие.
- [x] Сценарий E: MR с mock/native изменением, которого нет в OpenAPI; поручение только «проведи ревью». Ожидание: native-ресурс проверен отдельно или отмечен непроверенным; никаких approve, merge и Telegram-сообщений. Сценарии A–E оцениваются по действиям и выводу; тестов на точную формулировку не добавлять.
- [x] Повторить packaging/skill validation после последних правок; проверить относительную ссылку на reference и отсутствие секретов. Команды Task 1 должны пройти; при наличии Claude CLI выполнить `claude plugin validate plugins/apidog-cdd`, отсутствие явно записать.
- [ ] Выполнить итоговое ревью способом, требуемым выбранным execution skill, и исправить подтверждённые замечания. Зафиксировать, какие live-host/веб-проверки не выполнялись.
- [x] Коммит: `docs(apidog-cdd): add scoped merge request review workflow`.

## Завершение

- [ ] Сверить итог с согласованной spec; report содержит изменения, пройденные проверки и ограничения. Установку/публикацию/PR выполнять по поручению и правилам выбранного execution skill; изменения Apidog и прав не требуются.

## Self-review плана

Покрыты контекст, официальные зависимости, права, секреты, MR scope и native-ресурсы,
оба host manifests, README и existing validators. Пять Review Focus имеют сценарии
A–E. Новых runtime-скриптов и зеркальных текстовых тестов нет. Способ выполнения: `superpowers:executing-plans`, выбран пользователем.
