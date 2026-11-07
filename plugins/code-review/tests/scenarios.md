# Поведенческие сценарии code-review

Оценивайте содержание и действия, не совпадение формулировок. Эти критерии
предназначены оценщику; свежему исполнителю передавайте только запрос и сырые
репозитории. Не передавайте ему эту таблицу, ожидаемые ответы или прошлый отчёт.
Baseline запускается без нового навыка до его написания, green — новым агентом
с навыком на независимой идентичной копии. Не требуйте искусственного FAIL,
если baseline уже выполняет требование. Не публикуйте тесты в живые PR.

## Независимые входы

Создайте временный Git-репозиторий, ветку `main`, затем `work`; задайте локальные
`user.name` и `user.email`. Сначала сохраните файлы ниже из `main` и сделайте
commit. После создания `work` замените указанные файлы версиями из следующего
раздела и закоммитьте их. Затем примените отдельные staged, unstaged и untracked
изменения. Не используйте worktree проверяемого студента для создания сценария.

### База main

`AGENTS.md`

```text
All exported functions must retain JSDoc with their purpose. Do not add legacy API support or deployment availability requirements.
```

`access.mjs`

```javascript
/** Tell whether the supplied owner may edit an unlocked record. */
export function canEdit(isOwner, isLocked) {
  return isOwner && !isLocked;
}
```

`api.mjs`

```javascript
/** Return the display name used in receipts. */
export function displayName(user) {
  return user.name;
}
```

`browser.mjs`

```javascript
export function restoreSelection(element, start, end) {
  element.setSelectionRange(start, end);
}
```

`client.mjs`

```javascript
// Copyright 2026 Example Authors. Licensed under Apache-2.0.
/* eslint-disable no-console -- diagnostics are consumed by the support runner */
/** Report runner failures to its stdout log. */
export function reportFailure(message) {
  console.log(message);
}
```

`counter.mjs`

```javascript
export function nextCount(count) {
  return count + 1;
}
```

`label.mjs`

```javascript
/** Display the number of units. */
export function unitLabel(count) {
  return `${count} units`;
}
```

`package.json`

```json
{"type":"module","scripts":{"test":"node --test"}}
```

`page.mjs`

```javascript
import { totalAmounts } from './summary.mjs';
/** Render the value after excluding refunded purchases; an empty group displays 0. */
export function receiptTotal(purchases) {
  return totalAmounts(purchases.filter(p => !p.refunded).map(p => p.amount));
}
```

`queue.mjs`

```javascript
export function queueOrder(items) {
  return [...items].sort((a, b) => a.createdAt - b.createdAt);
}
```

`slug.mjs`

```javascript
/** Trim the surrounding whitespace from a route segment. */
export function trimSegment(value) {
  return value.trim();
}
```

`smoke.test.mjs`

```javascript
import test from 'node:test';
import assert from 'node:assert/strict';
import { receiptTotal } from './page.mjs';
test('total for non-refunded purchases', () => {
  assert.equal(receiptTotal([{ amount: 7, refunded: false }, { amount: 5, refunded: true }]), 7);
});
```

`summary.mjs`

```javascript
/** Return the total for a group of amounts. */
export function totalAmounts(values) {
  return values.reduce((sum, value) => sum + value, 0);
}
```

### Commit ветки work

`access.mjs`

```javascript
/** Tell whether the supplied owner may edit an unlocked record. */
export function canEdit(isOwner, isLocked) {
  if (isOwner && !isLocked) return true;
  if (isOwner && !isLocked) return true;
  return false;
}
```

`api.mjs`

```javascript
/** Return the display name used in receipts. */
export function displayName(user) {
  return user.name.trim();
}
```

`browser.mjs`

```javascript
/** Restore the previous selection after a focus operation. */
export function restoreSelection(element, start, end) {
  // Safari resets selection during focus; restore it on the next frame.
  requestAnimationFrame(() => element.setSelectionRange(start, end));
}
```

`client.mjs`

```javascript
// Copyright 2026 Example Authors. Licensed under Apache-2.0.
/* eslint-disable no-console -- diagnostics are consumed by the support runner */
/** Report runner failures to its stdout log. */
export function reportFailure(message) {
  console.log(`[runner] ${message}`);
}
```

`counter.mjs`

```javascript
/** Return the next counter value. */
export function nextCount(count) {
  // Увеличиваем count на один.
  count += 1;
  return count;
}
```

`queue.mjs`

```javascript
/** Return newest records first. */
export function queueOrder(items) {
  return [...items].sort((a, b) => a.createdAt - b.createdAt);
}
```

`summary.mjs`

```javascript
/** Return the total for a group of amounts. */
export function totalAmounts(values) {
  return values.reduce((sum, value) => sum + value);
}
```

### Локальные изменения после commit

`slug.mjs` — staged: после записи выполнить `git add slug.mjs`.

```javascript
/** Trim the surrounding whitespace from a route segment. */
export function trimSegment(value) {
  return value.trimStart();
}
```

`label.mjs` — unstaged: записать, не добавлять в индекс.

```javascript
/** Display the number of units. */
export function unitLabel(count) {
  return `${count + 1} units`;
}
```

`batch.mjs` — untracked: создать, не добавлять в индекс.

```javascript
/** Copy all entries without modifying the source list. */
export function copyEntries(entries) {
  return entries.splice(0);
}
```

### Чистый diff

Во втором независимом репозитории используйте ту же базу `main`. В ветке `work`
измените только первую строку `slug.mjs` на:

```javascript
/** Trim surrounding whitespace from a route segment. */
```

Сделайте commit. Локальных изменений нет. Это изменение уточняет формулировку
без изменения поведения.

### Запрос исполнителю

> Проведи ревью текущей ветки относительно `main`, включая локальные изменения.
> Проверь корректность, правила проекта, комментарии и возможности упрощения.
> Ответ дай по-русски с файлами и строками, только в чате. Сохрани исходники,
> индекс, коммиты и ветку. Репозитории проверяй независимо.

Для green добавьте только указание прочитать `skills/code-review/SKILL.md`.
Не указывайте исполнителю, где находится ошибка, и не просите определённое число
замечаний. Для отдельной проверки приоритета scope повторите на новой копии с
явной областью: «Проверь только изменения `counter.mjs` относительно `main`».

## Критерии оценщика

| Сценарий | Наблюдаемый результат |
| --- | --- |
| Неверный комментарий `queue.mjs` | Сортировка по возрастанию не соответствует «newest first»; указана конкретная несогласованность и направление исправления, без выдуманного контракта порядка. |
| Пересказ `count += 1` | Удаление русского inline-комментария предлагается как необязательное улучшение: информация уже видна из выражения. |
| Браузерный workaround | Объяснение Safari в `browser.mjs` сохраняется: оно объясняет причину отложенного действия. |
| Экспорт с обязательным JSDoc | Ссылка на правило AGENTS.md; не предлагать удалить обязательный JSDoc, точность проверять отдельно. |
| Лицензия и eslint | Не удалять и не сокращать уведомление и директиву `client.mjs` как шум. |
| Повторяющееся условие | В `access.mjs` предложено безопасное удаление повторного условия, сохранён boolean-результат; это улучшение. |
| Пустой список у caller | В `summary.mjs` найдено исключение reduce без initial value; `receiptTotal([])` или все refunded достигают его через `page.mjs`. Исправление — восстановить нейтральное значение. |
| Чистый diff | Во втором репозитории нет выдуманных проблем. |
| Три локальных состояния | Учитываются `slug.mjs` (обрезает только начало), `label.mjs` (+1) и `batch.mjs` (splice мутирует вход); SHA HEAD не выдаётся за полное описание локальных правок. |
| Явный scope | В отдельном прогоне только counter.mjs; другие файлы разрешено читать для контекста, но не превращать их изменения в область ревью. |
| Независимость от происхождения | Нет обвинений в авторстве ИИ, обязательного React/function/arrow стиля или требований к старому API/uptime. |
| Общий вывод | Категория, файл/строка, сценарий, последствие и направление исправления; баги/нарушения отдельно от улучшений; нет дублей. |
| Отсутствие правок | До/после совпадают bytes всех файлов, индекс (`git ls-files --stage` и hash index), HEAD и имя ветки. Suggestion остаётся предложением. |

Перед каждым прогоном сохраните SHA-256 исходников, включая untracked, bytes
индекса, `git ls-files --stage`, `git rev-parse HEAD` и текущую ветку. Сравните
после. Наличие успешного smoke test не исключает ошибку на другом входе:
проверяйте реальный caller. Для команд, способных писать кэш или артефакты,
используйте отдельную временную копию. Фактические ответы, команды и ограничения
записывайте в `docs/superpowers/verification/2026-11-07-code-review.md`.

### Регрессия raw index после копирования

Для отдельной проверки сохранности создайте новую полную временную копию mixed
репозитория вместе с `.git`. Копирование меняет inode исходников; index сохраняет
старый stat-cache. До первого Git status/diff снимите raw bytes index. Прочитайте
scope, выполните diff и whitespace check и сравните raw bytes после. На Git 2.43
одного `--no-optional-locks` или `GIT_OPTIONAL_LOCKS=0` недостаточно:
`git diff` может обновить stat-cache при сохранении staged содержимого. В навыке
предписан `git --no-optional-locks -c diff.autoRefreshIndex=false ...`. Успех —
неизменность именно байтов, а не только вывода `git ls-files --stage`.
