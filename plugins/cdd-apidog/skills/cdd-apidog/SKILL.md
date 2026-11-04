---
name: cdd-apidog
description: Use when working with Apidog contracts, branches, merge requests, Cloud Mock, project settings or access for Cellestial / Cringe-Driven-Development-Team, including project 1382426 and vb78fyael1.apidog.io.
---

# Apidog CDD

Проектный контекст поверх официальных скиллов Apidog. Применяется к CDD;
другой проект требует своих ссылок и правил.

## Карта проекта

| Что | Где |
|---|---|
| Проект `2026_2_Cringe_Driven_Development` | [Apidog, 1382426](https://app.apidog.com/project/1382426) |
| Согласованный контракт | Защищённая `main`, ID `1388508`; команда `832765` |
| Опубликованный контракт из main | https://vb78fyael1.apidog.io/ — не содержит ещё не влитые изменения MR |
| Backend: ветки, генерация, особенности слияния | [docs/apidog.md](https://github.com/Cringe-Driven-Development-Team/backend/blob/main/docs/apidog.md) |
| Frontend/BFF: генерация и Cloud Mock | [docs/api-contract.md](https://github.com/Cringe-Driven-Development-Team/frontend/blob/main/docs/api-contract.md) |
| Правила команды | [CONTRIBUTING.md](https://github.com/Cringe-Driven-Development-Team/.github/blob/main/CONTRIBUTING.md) |
| Архитектура проекта | [Контекст Cellestial](https://docs.cellestial.ru/project-context) |
| Обсуждения Apidog | [Тема Telegram](https://t.me/c/3713420351/6033) — отправка только по поручению |

ID сверены 2026-11-04. Перед работой сверяй выбранную ветку и относящийся
к задаче источник из таблицы. При расхождении сообщи о нём; актуальные правила
репозитория и живые данные приоритетнее сохранённого описания. Состав участников,
их права и открытые MR получай заново.

## Инструменты и официальные скиллы

Найди доступные скиллы в каталоге текущего host, не по абсолютному пути.
Для CLI загрузи `apidog-cli`, затем только нужное дополнение:

| Задача | Дополнение |
|---|---|
| Ветки и действия с MR | `apidog-branch` |
| Экспорт/импорт | `apidog-import-export` |
| Кейсы / многошаговые сценарии / запуск и CI | `apidog-test-case` / `apidog-test-scenario` / `apidog-test-automation` |
| Несколько этапов изменения API | `apidog-workflow-api-lifecycle` |
| Ошибка CLI или расхождение сохранения/отображения | `apidog-cli-checkup` |

Для ревью MR читай [порядок проверки](references/review.md) и `apidog-branch`.

Если скилла нет, сообщи и предложи `apidog skill install` (локально в текущем
workspace). Для глобальной установки нужному host:
`npx -y skills add https://apidog.com --agent codex --skill '*' --global --yes`
или с `--agent claude-code`. Самостоятельно не устанавливай; доступное чтение
продолжай через текущий `apidog --help` и help подкоманды. Credentials не выводи.

MCP удобен для OpenAPI и `$ref`: проверь проект/ветку подключения, обнови snapshot
через доступный refresh и прочитай нужные схемы. Название Default module не
доказывает ветку. Для MR, веток и native-ресурсов используй CLI. Сверяй текущие
schemas инструментов: имена серверов меняются.

## Разработка по контракту

Spec First: сначала контракт, затем реализация. Браузер обращается к BFF;
Apidog описывает контракт BFF → Go. Не выводи отсутствие API из устаревшей
локальной спеки. Чтение контракта не требует перегенерации рабочего дерева.

Для изменения кода читай соответствующее руководство из карты: frontend —
`bun run sync`, backend — `make generate`. `APIDOG_BRANCH_ID` выбирает ветку;
пустое значение означает main. Генерируемые файлы руками не правь. Разработка
по sprint допустима; перед слиянием backend PR руководство требует генерацию
из main Apidog. GitHub-задачи/PR веди через `cdd-tasks`, если это часть поручения.

Контракт и Cloud Mock должны относиться к одной ветке; URL мока бери из Apidog,
не добавляй `/api/v1`. Несоответствие мока исправляется отдельным MR по правилам
frontend. Успешный mock-тест не доказывает сохранение данных или отзыв сессий в Go.
Не вводи legacy-режимы и требования безостановочной выкладки для учебного проекта.

## Проект, участники, права

Чтение: `apidog project get 1382426`, `apidog team get 832765`;
настройки — `apidog project settings get --project 1382426`.
**До вызова настроек подготовь фильтрацию stdout:** ответ может содержать
`cloudMock.token`. Выводи только запрошенные поля, без сырого ответа в логах,
файлах ревью или ошибках; отсутствие флага не равно `false`.

В проверенном CLI 2.2.12 `team get` возвращает роль и `teamPermissions` текущего
аккаунта, не персональные права всех участников проекта. Для полного списка
сверь актуальные команды и доступный разрешённый UI/документированный API;
учти страницы выдачи и различие ролей команды/проекта. Если списка нет,
отметь непроверенную часть, не придумывай ручки. Изменение участников и прав
этим скиллом не покрывается.
