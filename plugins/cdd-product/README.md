# Cellestial Product

`cdd-product@cdd` добавляет скилл `cellestial-product` для знакомства с Cellestial
и обсуждения новых возможностей из любого репозитория.

Он начинает с [обзора продукта](https://docs.cellestial.ru/documentation/), затем читает
источники выбранного сценария. Факты о продукте остаются в docs. Для макетов используется
доступный `figma-ops`, для обсуждения решений — доступный `superpowers:brainstorming`;
эти плагины устанавливаются отдельно. Недоступность Figma не останавливает обсуждение
по документам.

## Подключение

После подключения маркетплейса `cdd` по [общей инструкции](../../README.md):

```bash
codex plugin marketplace upgrade cdd
codex plugin add cdd-product@cdd
```

Claude Code:

```text
/plugin marketplace update cdd
/plugin install cdd-product@cdd
```

Откройте новую сессию. Пример запроса: «Обсудим новые фичи Cellestial» или
«Обсудим поиск внутри блокнота».

Скилл перенесён из `.agents/skills/cellestial-product` и `.claude/skills/cellestial-product`
репозитория docs. После подключения плагина используйте версию docs без этих локальных
копий, чтобы навык не показывался дважды.
