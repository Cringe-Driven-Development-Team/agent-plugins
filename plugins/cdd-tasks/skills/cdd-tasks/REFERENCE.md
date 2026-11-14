# cdd-tasks: команды

Команды проверены на `gh` 2.x. Организация — `Cringe-Driven-Development-Team`, доска — проект
номер 1 (Scrumban). Для команд `gh project` токену нужен scope `project`:
`gh auth refresh -s project`.

## 1. Шаблон описания задачи

```markdown
## Цель

Что изменится, когда задача будет сделана, и зачем.

## Что сделать

- [ ] Шаг, который можно проверить.

## Приёмка

- Наблюдаемый результат: что открыть или запустить и что увидеть.

## Зависимости

1. Задачи и PR, без которых эту не сделать.

## Не входит

- Что рядом, но делается другой задачей.
```

«Цель», «Что сделать» и «Приёмка» обязательны. В задаче на несколько репозиториев добавь раздел
«Порядок мержа» для корректного закрытия родителя. Не требуй непрерывной работы прода
между выкладками, если владелец прямо не попросил об этом.

## 2. Задача и sub-issue

Создать задачу (описание — из файла, чтобы не ломать разметку кавычками):

```bash
gh issue create -R Cringe-Driven-Development-Team/frontend \
  --title "Frontend. Выкатка клиента в S3" --body-file body.md --assignee <логин>
```

Привязать существующую задачу как sub-issue. API принимает числовой `id` задачи, а не её номер:

```bash
SUB_ID=$(gh api repos/Cringe-Driven-Development-Team/infra/issues/22 --jq .id)
gh api -X POST repos/Cringe-Driven-Development-Team/frontend/issues/6/sub_issues \
  -F sub_issue_id="$SUB_ID" --jq .sub_issues_summary
```

Здесь `frontend#6` — родитель, `infra#22` — sub-issue. `-F`, не `-f`: значение должно уйти числом.

Проверить связь:

```bash
gh api repos/Cringe-Driven-Development-Team/frontend/issues/6/sub_issues --jq '.[] | "\(.repository_url | split("/") | last)#\(.number) \(.state)"'
```

Для реальных зависимостей задач используй GitHub `Blocked by`. Номер задачи — не её
числовой `id`: сначала получи `id` блокирующей задачи. Например, для `infra#64`,
которую блокирует `infra#54`:

```bash
ISSUE_REPO=Cringe-Driven-Development-Team/infra
ISSUE_NUMBER=64
BLOCKER_REPO=Cringe-Driven-Development-Team/infra
BLOCKER_NUMBER=54
BLOCKER_ID=$(gh api "repos/$BLOCKER_REPO/issues/$BLOCKER_NUMBER" --jq .id)
gh api "repos/$ISSUE_REPO/issues/$ISSUE_NUMBER/dependencies/blocked_by" \
  --jq '[.[] | {number, html_url}]' # проверь существующие связи перед добавлением
gh api -X POST "repos/$ISSUE_REPO/issues/$ISSUE_NUMBER/dependencies/blocked_by" \
  -F issue_id="$BLOCKER_ID"
gh api "repos/$ISSUE_REPO/issues/$ISSUE_NUMBER/dependencies/blocked_by" \
  --jq '[.[] | {number, html_url}]' # проверь результат
```

Добавляй только отсутствующие блокеры. Если согласованная зависимость снята:

```bash
gh api -X DELETE "repos/$ISSUE_REPO/issues/$ISSUE_NUMBER/dependencies/blocked_by/$BLOCKER_ID"
gh api "repos/$ISSUE_REPO/issues/$ISSUE_NUMBER/dependencies/blocked_by" \
  --jq '[.[] | {number, html_url}]'
```

Ссылки на PR и просто связанные задачи остаются в тексте;
`Blocked by` не заменяет `sub-issue`.

## 3. Доска

Backlog, Sprint и Next Sprint — представления одного проекта Scrumban №1:

| Представление | Фильтр |
|---|---|
| Backlog | `-status:Done -sprint:@current -sprint:@next` |
| Sprint | `sprint:@current` |
| Next Sprint (`next-sprint`) | `sprint:@next` |

`@next` относится к следующей итерации поля Sprint и меняется вместе с текущей.
Актуальные названия и фильтры можно проверить:

```bash
gh api graphql -f query='query{organization(login:"Cringe-Driven-Development-Team"){projectV2(number:1){views(first:100){nodes{name number layout filter}}}}}' \
  --jq '.data.organization.projectV2.views.nodes'
```

Новая задача попадает на доску сама, если в репозитории подключён workflow «Автоматизация».
Если связи с проектом нет — добавить. Если связь есть, но карточки не видно, смотри
«Карточка привязана, но не отображается» ниже.

```bash
gh project item-add 1 --owner Cringe-Driven-Development-Team --url <ссылка на задачу>
```

Статус и спринт меняются по id, а id ищутся по имени — не зашивай их: id спринта меняется каждый
спринт.

```bash
# id проекта
PROJECT=$(gh project view 1 --owner Cringe-Driven-Development-Team --format json --jq .id)

# id карточки задачи
ITEM=$(gh api graphql -f query='query{repository(owner:"Cringe-Driven-Development-Team",name:"frontend"){issue(number:6){projectItems(first:5){nodes{id project{number}}}}}}' \
  --jq '.data.repository.issue.projectItems.nodes[] | select(.project.number==1) | .id')

# поле Status и id нужного значения
gh project field-list 1 --owner Cringe-Driven-Development-Team --format json \
  --jq '.fields[] | select(.name=="Status") | {id, options: [.options[] | "\(.name)=\(.id)"]}'

# выставить статус
gh project item-edit --project-id "$PROJECT" --id "$ITEM" \
  --field-id <id поля Status> --single-select-option-id <id значения>
```

### Назначить спринт и плановые даты

Используй [scripts/set_sprint.py](scripts/set_sprint.py) из каталога загруженного
скилла, рядом с этим справочником. Нужны Python 3.9+, авторизованный `gh` со scope
`project` и системные данные часового пояса `Europe/Moscow` для `@current`/`@next`.
Если часовой пояс недоступен, скрипт завершится до записи: восстанови системную
базу часовых поясов или используй явно названный пользователем спринт; не выбирай
относительную итерацию по случайной локальной дате. Python-пакетов устанавливать не нужно.

Команды ниже выполняются из каталога скилла; агент может передать абсолютный путь
к скрипту, разрешённый относительно прочитанного `SKILL.md`. Примеры — реальные
формы команд, запускать только для задач, указанных в поручении.

```bash
# Следующий спринт и обе даты по его границам.
python3 scripts/set_sprint.py \
  https://github.com/Cringe-Driven-Development-Team/frontend/issues/6 --sprint @next

# Конкретный спринт и явно запрошенный диапазон.
python3 scripts/set_sprint.py \
  https://github.com/Cringe-Driven-Development-Team/frontend/issues/6 \
  --sprint 'Sprint 10' --start 2026-11-18 --end 2026-11-19

# Несколько указанных задач, один спринт; повторные ссылки обрабатываются один раз.
python3 scripts/set_sprint.py \
  https://github.com/Cringe-Driven-Development-Team/frontend/issues/6 \
  https://github.com/Cringe-Driven-Development-Team/infra/issues/22 --sprint 'Sprint 10'
```

`--sprint` принимает точное название, `@current` или `@next`. Текущая итерация
содержит сегодняшнюю московскую дату: `startDate <= today < startDate + duration`.
Следующая — с ближайшим началом не раньше исключённой правой границы текущей;
порядок массива не учитывается. При перерыве, неоднозначности или отсутствии
следующей итерации уточни название у пользователя; скрипт итерации не создаёт.

Без `--start`/`--end` записываются начало и **последний день включительно**:
`End Date = startDate + duration - 1 день`. Назначение Sprint 10 перезапишет
старые 12–13 ноября на 16–22 ноября. Явная пара дат имеет приоритет и не обрезается
границами спринта. Параметры дат задаются вместе; если названа одна дата,
уточни вторую до запуска. Начало позже конца и несуществующие даты отклоняются.

Скрипт читает все страницы Scrumban №1 и проверяет весь набор целей до первой
записи. Поля `Sprint`, `Start Date`, `End Date` должны существовать и иметь
правильные типы; ID находятся по живым данным. Карточка должна быть единственной
и неархивированной; отсутствующую карточку скрипт сам не добавляет.

Для каждой задачи читаются исходные `Sprint`, даты и `Status`, затем записываются
только три целевых поля и отдельно перечитывается результат. `OK` означает
совпадение `Sprint.iterationId`, обеих дат и исходного `Status.optionId`
(включая отсутствие статуса). Код выхода 0 — все задачи подтверждены,
2 — неверные аргументы, 1 — ошибка API, данных или проверки.

Запись трёх полей не транзакция: при ошибке или таймауте часть могла сохраниться.
Скрипт останавливает дальнейшие записи, пытается прочитать фактические значения
и выводит исходное/полученное состояние, подтверждённые и необработанные задачи.
Если чтение не удалось, результат **неизвестен**. Сообщи это пользователю;
не повторяй запись вслепую и не восстанавливай прежний статус поверх чужого изменения.

### Полосы Gantt

В Roadmap → **Date fields** выбери `Start date → Start Date`,
`Target date → End Date`. В **Markers** отдельно включи `Sprint` и сохрани вид.
Границы полос определяются плановыми датами задачи. Если обе даты пусты, строка
задачи остаётся слева, но полосы на календаре нет: перепривязывать карточку не нужно.
Заполнение дат требует поручения; диагностика сама по себе не разрешает запись.
Ручное изменение Sprint в GitHub не запускает скрипт и автоматически даты не меняет.

### Карточка привязана, но не отображается

Сначала проверь исполнителя, проект, `isArchived`, Status, Sprint (по датам), фильтр
представления и выбранный срез Assignees. Сравни ID и значения с видимой карточкой.
Отсутствие карточки в интерфейсе само по себе ещё не доказывает баг GitHub.

Проверь обе стороны связи: `issue.projectItems` и полный `projectV2.items` без фильтра,
с пагинацией до `hasNextPage: false`. Прямое чтение карточки через `node(id: ...)`
не заменяет проверку списка. Если неархивированная карточка указывает на нужный проект,
но отсутствует в его полном списке, зафиксируй расхождение API: это признак сбоя
на стороне GitHub; рассинхронизация индекса — вероятная, а не доказанная причина.

Подтверждённый обход: удалить привязку к проекту и добавить её заново, затем восстановить
спринт. Пользователь проверил это 2026-11-07 на
[frontend#164](https://github.com/Cringe-Driven-Development-Team/frontend/issues/164):
после перепривязки Scrumban и повторного назначения Sprint карточка появилась.

Если восстановление видимости входит в поручение:

1. До удаления сохрани ID карточки, все её заполненные поля проекта и отсутствие
   значений там, где оно существенно: Status, Sprint, Priority и другие поля.
   Перепривязка может потерять эти значения и историю карточки.
2. В боковой панели самой Issue открой Projects, сними Scrumban, затем добавь Scrumban
   заново. Удаляется только привязка к этому проекту, сама Issue остаётся.
3. Заново получи ID карточки; не используй прежний ID. Восстанови сохранённые поля,
   включая Sprint и Status, с учётом явно запрошенных изменений. Учти, что автоматизация
   добавления может асинхронно выставить Backlog.
4. Проверь значения и наличие новой карточки в полном `projectV2.items`, затем её
   отображение в нужном представлении. Если доступа к интерфейсу нет, отдельно сообщи,
   что проверено через API, а видимость ещё не подтверждена.

Одной попытки достаточно: если обход не помог, сохрани диагностику для поддержки
GitHub и сообщи результат; не повторяй удаление по кругу и не создавай дубликат Issue.
Просьба только проверить причину не разрешает перепривязку. Известны
[похожие сообщения о пропавших карточках](https://github.com/orgs/community/discussions/193185),
но успешный обход в одном случае не гарантирует восстановление при любом сбое.

## 4. Pull request

Командный репозиторий фронта, задача `frontend#12`:

```bash
git switch -c web-12 origin/main
# …коммиты…
git push -u origin web-12
gh pr create -R Cringe-Driven-Development-Team/frontend --base main \
  --title "WEB-12: Форма входа" --body-file pr.md
```

Первая строка `pr.md` — `Closes #12`. Ментор frontend обязательно проверяет PR.
Backend также в Cringe-Driven-Development-Team/backend:
`api-12`, `API-12: …`, `Closes #12`; обязательный review Александра, кроме
персонального backend-исключения `YarikMix`, описанного ниже.

Проверить, что PR привязан к задаче:

```bash
gh pr view <номер> -R <репозиторий> --json closingIssuesReferences \
  --jq '[.closingIssuesReferences[] | "\(.repository.name)#\(.number)"]'
```

Пустой список при строке `Closes …` — проверить номер задачи и репозиторий PR.
При `Part of …` пустой список — норма.

Задача закрывается при мерже в ветку по умолчанию. Frontend и backend требуют
апрува ментора, в том числе после переноса в командную организацию. По отдельному
решению владельца `YarikMix` может обычным merge принять backend PR без Approve,
включая свой. Перед merge проверь authenticated account и действующий персональный
approval ruleset: PR, актуальная ветка, `lint/test/docker` и разрешение обсуждений
остаются обязательными. `--admin`, bypass CI/integrity и перенос исключения на
frontend или других участников не допускаются. Если `gh pr merge` останавливается
на общем `Review required`, при подтверждённом YarikMix-исключении можно вызвать
стандартный `PUT repos/Cringe-Driven-Development-Team/backend/pulls/N/merge`:
`sha` равен проверенному актуальному head, `merge_method=merge`. Перед вызовом снова
проверь аккаунт, персональный approval ruleset, required checks, актуальность ветки
и обсуждения. Не меняй rulesets ради обхода ошибки и не передавай admin override.
Учебные frontend и backend — копии main без Actions; рабочие PR и review остаются в команде.

## 5. Задача без PR

```bash
gh issue comment 3 -R Cringe-Driven-Development-Team/figma --body "Готово: <ссылка на результат>"
```

Затем карточку — в `In review` (§3). Закрывает ментор:

```bash
gh issue close 3 -R Cringe-Driven-Development-Team/figma --comment "Принято."
```

Задача больше не нужна: `gh issue close <номер> -R <репозиторий> --reason "not planned" --comment "<почему>"`.

## 6. После merge: CI и учебная копия

Проверки выполняются в командном репозитории. В учебном Actions выключены; туда
копируется история main с теми же SHA и деревьями, без новых PR, ревью и runs.
Merge закрывает связанную задачу независимо от последующего результата sync.

Примеры — Bash (Linux/WSL). Выбери область и фактический merge SHA из PR:

```bash
AREA=frontend  # либо backend
PRIMARY="Cringe-Driven-Development-Team/$AREA"
case "$AREA" in
  frontend) COURSE=frontend-park-mail-ru/2026_2_Cringe_Driven_Development ;;
  backend) COURSE=go-park-mail-ru/2026_2_Cringe_Driven_Development ;;
  *) echo 'Неизвестная область' >&2; exit 1 ;;
esac
MERGE_SHA='полный merge SHA проверяемого PR'
gh run list -R "$PRIMARY" --workflow ci.yml --branch main --event push \
  --commit "$MERGE_SHA" --json databaseId,headSha,status,conclusion,url
CI_RUN_ID='ID push/main CI для этого SHA'
gh run view "$CI_RUN_ID" -R "$PRIMARY" \
  --json event,headBranch,headSha,workflowName,status,conclusion,jobs,url
```

Зелёный Check исходного PR не заменяет push/main CI. Сверь run с ci.yml, push,
main и проверяемым SHA; отсутствие запуска или незавершённый job — ещё не успех.
Проверь code jobs: frontend — Check, backend — lint/test/docker; отдельно
course-sync / sync и upload/deploy, если они запускались. Если упал только sync,
общий CI может быть красным при успешных code jobs и deploy.

Проверь актуальность копии:

```bash
PRIMARY_SHA=$(gh api "repos/$PRIMARY/commits/main" --jq .sha) || exit 1
COURSE_SHA=$(gh api "repos/$COURSE/commits/main" --jq .sha) || exit 1
test "$PRIMARY_SHA" = "$COURSE_SHA"
```

Одинаковый commit SHA означает одинаковое дерево. Если main ушёл вперёд во время
проверки, выбери CI нового SHA и повтори сверку; результат исходного PR укажи отдельно.
При несовпадении не объявляй копию актуальной: найди соответствующий sync и его причину.

### Повтор sync без deploy

Сначала сверь текущие main: если новый SHA уже синхронизирован, старый run повторять
не нужно. Иначе прочитай лог упавшего sync; исправление доступа или истории бери из
[runbook](https://github.com/Cringe-Driven-Development-Team/.github/blob/main/docs/migrations/team-repositories-runbook.md).
PR остаётся merged, задача — closed; не переоткрывай их ради повторного копирования.

Для повтора того же CI run возьми databaseId именно job course-sync / sync:

```bash
gh run view "$CI_RUN_ID" -R "$PRIMARY" --json jobs \
  --jq '.jobs[] | {databaseId,name,status,conclusion}'
SYNC_JOB_ID='databaseId упавшего course-sync / sync'
gh run view "$CI_RUN_ID" -R "$PRIMARY" --job "$SYNC_JOB_ID" --log-failed
gh run rerun "$CI_RUN_ID" -R "$PRIMARY" --job "$SYNC_JOB_ID"
```

Это повтор конкретного sync job. Общий Re-run all jobs или --failed может затронуть
другие jobs, включая deploy. Альтернатива — отдельный ручной sync:

```bash
gh workflow run sync-to-course.yml -R "$PRIMARY" --ref main -f "ci_run_id=$CI_RUN_ID"
```

Ручной workflow не запускает deploy. Передай ID проверенного push/main ci.yml с
успешными обязательными code jobs (backend также docker); общий conclusion может
быть failure из-за sync. Произвольный SHA/ref/target не передаётся: SHA извлекается
из CI, provenance проверяется заново. Не повторяй старый SHA поверх более нового
main; при невозможном fast-forward разбери расхождение по runbook, без force push.
После повтора проверь его sync job и заново сравни текущие main. В отчёт — URL
проверенного запуска, SHA и результат; отсутствие Telegram-сообщения не доказывает успех.

### Уведомления sync

| Событие | Ожидаемое сообщение |
|---|---|
| Ошибка синхронизации | ❌ Course synchronization failed |
| Успешный повтор того же run после ошибки sync | ✅ Course synchronization recovered |
| Обычный успех или повтор, у которого предыдущая синхронизация уже успешна | Сообщения нет |
| Новый отдельный ручной run после ошибки другого run | Успех не даёт recovery-сообщения о другом run |

Уведомление о восстановлении относится к истории попыток одного run. Старые runs
используют прежний закреплённый SHA автоматики: их Re-run не подключает новую версию
уведомлений. Ошибка чтения истории или доставки recovery видна в job как warning;
сам sync может быть успешным. Условия и устройство общей автоматики —
[README .github](https://github.com/Cringe-Driven-Development-Team/.github/blob/main/README.md).
