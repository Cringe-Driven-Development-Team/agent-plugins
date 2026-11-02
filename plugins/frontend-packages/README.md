# frontend-packages

Скилл `npm-publishing` для подключения пакетов
`Cringe-Driven-Development-Team/frontend-packages` к автоматической публикации
в npm, проверки доверия и восстановления частичных выпусков. Работает в Codex
и Claude Code; команды и ограничения целевого проекта читает из его runbook.

«Подключи @cdd-team/<пакет> к автопубликации» поручает агенту весь процесс,
включая необходимые PR/merge и публикации. Человек подтверждает npm 2FA.
Запрос «проверь, почему упал выпуск» остаётся диагностикой без изменений.

Нужны checkout проекта, его инструменты Bun/Node/npm и доступ к npm/GitHub
для порученных операций. Один GitHub Release не считается подтверждением:
цель — реальный OIDC publish, версия в registry и успешные проверки выпуска.

Подключение `frontend-packages@cdd` — по [инструкции маркетплейса](../../README.md).
Основные правила: [SKILL.md](skills/npm-publishing/SKILL.md), команды:
[REFERENCE.md](skills/npm-publishing/REFERENCE.md).

## Проверка

Из корня маркетплейса: `bash tests/manifest_validation_test.sh` и
`bash tests/manifest_test.sh`, затем `claude plugin validate plugins/frontend-packages`.
Поведенческие сценарии в `evals/`: `bootstrap`, `trust-recovery`, `partial-release`,
`diagnostic-only`. Они используют смоделированные артефакты и не требуют
публикаций. Запускать по одному, например:

```bash
claude plugin eval plugins/frontend-packages --case partial-release --runs 3 --max-cost-usd 4
```

Eval — отдельные платные вызовы модели. Наличие файлов сценариев и валидные
манифесты сами по себе не доказывают успешного поведения агента.
