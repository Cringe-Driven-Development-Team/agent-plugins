# Происхождение code-review@cdd

Неофициальная адаптация Cringe-Driven-Development-Team для Claude Code и Codex.
Содержимое плагина распространяется под Apache-2.0; полный неизменённый текст
апстрима сохранён в `LICENSE` и `skills/code-review/LICENSE` для отдельной
передачи навыка. Обновления переносятся вручную после проверки diff;
`scripts/sync.sh` и `upstream.json` не используются для этой адаптации.

## Закреплённые источники

Репозиторий: [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official).
Просмотренный commit: `0412be76f50ab4f4f8abff3753efa9269fbbca5b`.
Все ссылки ниже закреплены на этом commit.

| Источник | Что адаптировано |
| --- | --- |
| [code-review/commands/code-review.md](https://github.com/anthropics/claude-plugins-official/blob/0412be76f50ab4f4f8abff3753efa9269fbbca5b/plugins/code-review/commands/code-review.md) | Область ревью, чтение инструкций проекта, проверка выводов и объединение дублей. |
| [code-simplifier/agents/code-simplifier.md](https://github.com/anthropics/claude-plugins-official/blob/0412be76f50ab4f4f8abff3753efa9269fbbca5b/plugins/code-simplifier/agents/code-simplifier.md) | Упрощение с сохранением поведения, ошибок и соглашений проекта. |
| [pr-review-toolkit/agents/comment-analyzer.md](https://github.com/anthropics/claude-plugins-official/blob/0412be76f50ab4f4f8abff3753efa9269fbbca5b/plugins/pr-review-toolkit/agents/comment-analyzer.md) | Точность и долговременная польза комментариев, проверка причин и рекомендаций удаления, только анализ. |

## Лицензии и уведомления

Прочитаны корневой LICENSE и отдельные LICENSE всех трёх плагинов на указанном
commit: каждый содержит Apache License, Version 2.0, January 2004; файлы
побайтово одинаковы (SHA-256
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`).
В LICENSE есть исходный шаблон `Copyright [yyyy] [name of copyright owner]`;
это незаполненный пример, а не новое утверждение об авторстве. В трёх исходных
Markdown-файлах нет отдельных copyright-уведомлений. Полное дерево commit
проверено: относящихся NOTICE в корне, `plugins/` и трёх каталогах плагинов нет.
Все три `.claude-plugin/plugin.json` указывают автора Anthropic
(`support@anthropic.com`). [README pr-review-toolkit](https://github.com/anthropics/claude-plugins-official/blob/0412be76f50ab4f4f8abff3753efa9269fbbca5b/plugins/pr-review-toolkit/README.md)
указывает автора Daisy (`daisy@anthropic.com`) и содержит раздел `License: MIT`.
Это расходится с отдельным [LICENSE toolkit](https://github.com/anthropics/claude-plugins-official/blob/0412be76f50ab4f4f8abff3753efa9269fbbca5b/plugins/pr-review-toolkit/LICENSE),
содержащим Apache-2.0. Сохраняем полный Apache-2.0 из LICENSE, не заменяем его MIT.

## Изменения адаптации

`skills/code-review/SKILL.md` и `skills/code-review/references/analysis.md`
переписаны и объединяют инструкции трёх источников; каждый содержит отметку
изменённого происхождения со ссылкой на этот файл. Добавлены локальные ветки,
staged/unstaged/untracked, явная область пользователя, AGENTS.md, русскоязычный
вывод и отделение обязательных замечаний от улучшений. Проверяется нужный контекст
вне diff, включая вызывающий код и входозависимые крайние случаи. Защищены
обязательный JSDoc, лицензии, директивы и объяснения причин. Распознавание авторства
ИИ не используется.

Не перенесены привязка к моделям, фиксированные четыре агента, предположение
безошибочности инструментов, пропуск повторного ревью, запрет искать ошибки на
конкретном вводе, Sentry/React и другие чужие стилевые правила, автоматическое
упрощение и применение suggestion. Рассматривается содержание, а не автор кода.

В процедуру повторного PR-ревью добавлены проверка исправлений в обсуждениях любых
авторов, ответ с SHA и доказательством и последующее закрытие треда. Добавлены
проверки актуального разговора, подтверждение результата записи и предотвращение
дублирующих ответов; ограничения «только в чате» и неразобранного pending сохранены.
