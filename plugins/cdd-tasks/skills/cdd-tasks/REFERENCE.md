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

Спринт — поле-итерация, `field-list` его значения не показывает:

```bash
gh api graphql -f query='query{organization(login:"Cringe-Driven-Development-Team"){projectV2(number:1){field(name:"Sprint"){... on ProjectV2IterationField{id configuration{iterations{id title startDate duration}}}}}}}' \
  --jq '.data.organization.projectV2.field | {id, iterations: .configuration.iterations}'
```

Текущая итерация содержит сегодняшнюю дату: `startDate <= today < startDate + duration дней`.
Дата окончания не включается. Следующая — итерация с ближайшей датой начала после
окончания текущей (включая саму дату окончания); порядок элементов `iterations` не учитывай.
Если текущей итерации нет (например, перерыв) или следующая не задана, сообщи об этом
и уточни целевой спринт до изменения карточки. Самостоятельно итерации не создавай.

Просьба «поставь на следующий спринт» меняет только поле Sprint: команду изменения
Status выше для неё не выполняй. До назначения прочитай значения карточки и сохрани
исходный `status.optionId` (включая отсутствие статуса):

```bash
gh api graphql -F item="$ITEM" -f query='query($item: ID!) {
  node(id: $item) {
    ... on ProjectV2Item {
      sprint: fieldValueByName(name: "Sprint") {
        ... on ProjectV2ItemFieldIterationValue { iterationId title }
      }
      status: fieldValueByName(name: "Status") {
        ... on ProjectV2ItemFieldSingleSelectValue { optionId name }
      }
    }
  }
}' --jq '.data.node'
```

Назначь найденный id следующей итерации:

```bash
gh project item-edit --project-id "$PROJECT" --id "$ITEM" \
  --field-id <id поля Sprint> --iteration-id <id следующей итерации>
```

После назначения повтори запрос чтения карточки: `sprint.iterationId` должен совпасть
с выбранным id, а `status.optionId` — с исходным, если пользователь не просил изменить статус.
Успешный ответ записи этого не доказывает. При расхождении сообщи фактические значения;
не объявляй назначение завершённым и не перезаписывай статус вслепую.

### Привязать трек к графу модулей

Файлы модулей ведёт `docs-modules`; здесь — только Projects и проверка результата.
Просьба добавить трек с указанными задачами уже разрешает нужную привязку «Трек».
Прочитай актуальный docs-modules и контракт пакета в репозитории docs: `board`
из `site/modules/module-graph.yaml`, `sprints` модуля и id файла трека. Не выводи
id трека из его заголовка. `issues` внутри подзадачи показывает карточку задачи,
но прогресс трека определяется полем «Трек» на доске.

До записи прочитай текущие поля, родителей и всех sub-issues с пагинацией (§2).
Сохрани Status, Sprint, Assignees и посторонние поля. У sub-issue без собственного
«Трека» используется родительский; модуль определяется собственным спринтом задачи,
без спринта — текущий. Если id трека отсутствует в этом модуле, задача не попадёт
в его прогресс. Не меняй спринт ради графа.

Если родитель включает завершённых детей прошлых модулей, не назначай весь набор
новому треку. Привяжи явно целевых текущих детей; привязку смешанного родителя
оставь до отдельного решения. Проверь эффект наследования даже для детей с пустым
полем. Существующий другой трек — отдельный конфликт: уточни перенос этой задачи,
остальные согласованные привязки выполни независимо.

Найди PROJECT и ITEM по текущей доске (§3 выше), field/option — по именам:

```bash
gh project field-list 1 --owner Cringe-Driven-Development-Team --limit 100 --format json \
  --jq '.fields[] | select(.name=="Трек") | {id,options}'
TRACK_FIELD='ID поля Трек из ответа'
TRACK_OPTION='ID варианта, name которого равен id трека'
```

Если варианта нет, подготовь файлы и PR по docs-modules. Новые варианты добавляет
штатный job board workflow Pages в docs на main. Дождись отдельно разрешённого
merge и успешного CI, затем перечитай options. Не запускай локальный
`module-graph board sync` и не создавай option вручную: sync заменяет список
вариантов целиком. Поручение привязать задачи не разрешает merge docs PR.
Сообщи отдельно, что подготовлено, что ждёт merge/CI и что ещё не опубликовано.

До и после записи прочитай карточку (для остальных полей/Assignees также сравни
исходный снимок и issue):

```bash
gh api graphql -F item="$ITEM" -f query='query($item: ID!) {
  node(id: $item) { ... on ProjectV2Item {
    track: fieldValueByName(name: "Трек") {
      ... on ProjectV2ItemFieldSingleSelectValue { optionId name }
    }
    status: fieldValueByName(name: "Status") {
      ... on ProjectV2ItemFieldSingleSelectValue { optionId name }
    }
    sprint: fieldValueByName(name: "Sprint") {
      ... on ProjectV2ItemFieldIterationValue { iterationId title }
    }
  } }
}' --jq '.data.node'
```

Для необходимой явной привязки меняй только «Трек»; уже правильное значение или
достаточное безопасное наследование не требуют повторной записи:

```bash
gh project item-edit --project-id "$PROJECT" --id "$ITEM" \
  --field-id "$TRACK_FIELD" --single-select-option-id "$TRACK_OPTION"
```

Перечитай GitHub: проверь optionId, сохранность остальных полей и наследование.
После этого проверь свежий snapshot и граф по docs-modules. Снимок — read-only,
в репозитории docs (board.json не коммитить):

```bash
GH_TOKEN="$(gh auth token)" bunx module-graph board snapshot site/modules/board.json
```

Если данные GitHub правильные, а сайт ещё показывает старый снимок, дождись Pages;
не добавляй фиктивные issues или новый спринт ради отображения. Успешный item-edit
не доказывает публикацию: отчёт различает файлы/PR, запись поля, свежий snapshot
и опубликованный граф. Если проверить сайт не удалось, скажи об этом явно.

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

Первая строка `pr.md` — `Closes #12`. По умолчанию PR проверяет ментор frontend.
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

Frontend issue штатно закрывает успешный CD (§7), backend и остальные — merge
закрывающего PR в default branch. Учебные репозитории остаются копиями main без
рабочих PR/Actions; review выполняется в команде.

### Разрешение и проверка merge

По умолчанию frontend и backend требуют апрува ментора. Технический доступ сам по
себе не разрешает merge. Явное поручение владельца и действующее в сессии разрешение
на bypass review имеют приоритет над ограничениями этого скилла/CONTRIBUTING:
не проси их повторно. Такое личное исключение не распространяется на команду.
Поручение только проверить PR или подготовить его не разрешает merge.

При поручении на merge проверь аккаунт, применимые правила и доступный метод:

```bash
PR_REPO='Cringe-Driven-Development-Team/frontend'  # фактический репозиторий
PR_NUMBER='номер PR'
gh api user --jq .login
gh pr view "$PR_NUMBER" -R "$PR_REPO" \
  --json state,isDraft,headRefOid,baseRefName,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup
PR_HEAD='полный проверяемый headRefOid'
gh pr checks "$PR_NUMBER" -R "$PR_REPO" --required
```

Сверь, что успешные обязательные checks принадлежат именно PR_HEAD, база верна,
PR открыт, конфликты отсутствуют, прочие обязательные требования выполнены.
Непосредственно перед операцией перечитай head; при изменении повтори проверки
для нового SHA. Красный/идущий CI и неизвестная mergeability не дают оснований
для merge, даже при разрешении bypass review. Rulesets ради merge не меняй.

Обычный merge (метод замени на допустимый в репозитории):

```bash
gh pr merge "$PR_NUMBER" -R "$PR_REPO" --merge --match-head-commit "$PR_HEAD"
```

Если для порученного merge необходим разрешённый владельцем обход review:

```bash
gh pr merge "$PR_NUMBER" -R "$PR_REPO" --merge --admin --match-head-commit "$PR_HEAD"
```

Mismatch SHA — повод заново проверить head, а не убрать защиту. Если GitHub не
разрешает операцию, сообщи конкретный ответ; разрешение владельца не даёт прав
изменять правила или обходить CI. После успеха проверь:

```bash
gh pr view "$PR_NUMBER" -R "$PR_REPO" \
  --json state,mergedAt,mergeCommit,closingIssuesReferences,url
```

Нужны фактический MERGED, merge SHA и относящиеся post-merge проверки (§6–7),
а не только exit 0 команды. Запуск CD отдельно не разрешён поручением на merge.

У команды также есть персональное backend-исключение: authenticated `YarikMix`
может обычным merge принять backend PR без Approve, включая свой. Перед ним сверь
действующий персональный approval ruleset: PR, актуальная ветка, успешные
`lint/test/docker` и разрешённые обсуждения остаются обязательными. Если CLI
останавливается на общем `Review required`, при подтверждённом исключении допустим
стандартный `PUT repos/Cringe-Driven-Development-Team/backend/pulls/N/merge` с
`sha=PR_HEAD`, `merge_method=merge`, после повторной проверки аккаунта, ruleset,
head и checks. Само это исключение не разрешает admin override, bypass CI или
его перенос на frontend/других участников; отдельную инструкцию владельца оценивай
по порядку выше.

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
Backend merge закрывает связанную задачу. Frontend после merge остаётся открытым
в Ready for build; Release/CD и закрытие проверяются отдельно (§7). Результат sync
не меняет момент закрытия задачи.

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
PR остаётся merged; состояние issue определяется её lifecycle: backend обычно closed,
frontend до CD обычно open. Не закрывай и не переоткрывай issue ради повторного копирования.

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


## 7. Frontend: Release, production и восстановление задач

`Ready for build` после merge и `Ready for release` после публикации — открытые
задачи. Release подтверждает готовность артефактов, а не работу production.
Штатное `completed` / `Done` требует Health check и сохранённого production success.
Ручной completed до CD остаётся Done; ручной reopen после merge защищён от его
повторов. Новый связанный merge после reopen начинает новый цикл.
Rollback сохраняет закрытость и ставит `Rollback from production`; следующий
успешный CD возвращает Done. Поздние merge/closed не перезаписывают новый результат.

### Проверить выпуск и production

```bash
RELEASE_REPO=Cringe-Driven-Development-Team/frontend
RELEASE_SHA='полный SHA выпуска, не обязательно текущего main'
DEPLOYMENT_ID='ID проверяемой production-операции'
gh release view "release-$RELEASE_SHA" -R "$RELEASE_REPO" \
  --json tagName,isDraft,isPrerelease,publishedAt,url,assets
gh api "repos/$RELEASE_REPO/deployments/$DEPLOYMENT_ID" \
  --jq '{id,sha,environment,task,payload,created_at}'
gh api "repos/$RELEASE_REPO/deployments/$DEPLOYMENT_ID/statuses?per_page=100" \
  --jq '.[0] | {state,created_at,log_url,environment_url}'
gh api --paginate "repos/$RELEASE_REPO/deployments?environment=production&per_page=100" \
  --jq '.[] | {id,sha,task,created_at,payload}'
```

Для исходного и последнего production Deployment проверь latest status, SHA,
`environment=production`, `task`/`payload.action` (`deploy` или `rollback`), ссылку
`payload.run` и соответствие Release. Из этой ссылки возьми RUN_ID и проверь
именно этот run/attempt, jobs Health check, Production result и Update release issues:

```bash
PRODUCTION_RUN_ID='ID из payload.run'
gh run view "$PRODUCTION_RUN_ID" -R "$RELEASE_REPO" \
  --json event,workflowName,headSha,status,conclusion,jobs,url
```

SHA запуска CD может быть SHA workflow на main; целевой выпуск определяется
Deployment и Release. Один зелёный Health check при сбое записи production success
не даёт Done. Красный общий run из-за Update release issues тоже не отменяет
подтверждённый production success: сообщи оба результата отдельно.

### Восстановить задачи без повторной выкатки

При поручении восстановить статусы сначала прочитай ошибку Update release issues.
Нужен исходный успешный production Deployment ID. Проверь также последнюю попытку:
пока она незавершённая или неуспешная, recovery не должен менять карточки.
Если появился более новый успешный deployment, не подменяй исходный ID: recovery
проверяет обе операции и актуальные состояния задач, пропуская уже неактуальные
изменения. Проверяй `changed`, `skipped`, `errors`, а не обещай обновить каждую задачу.

```bash
gh workflow run reconcile-issues.yml -R "$RELEASE_REPO" --ref main \
  -f "deployment_id=$DEPLOYMENT_ID"
gh run list -R "$RELEASE_REPO" --workflow reconcile-issues.yml \
  --event workflow_dispatch --branch main \
  --json databaseId,createdAt,status,conclusion,url
```

Сопоставь новый run с временем запуска и переданным input, затем проверь его:

```bash
RECOVERY_RUN_ID='ID запущенного recovery'
ISSUE_NUMBER='номер затронутой задачи'
gh run view "$RECOVERY_RUN_ID" -R "$RELEASE_REPO" --json jobs,conclusion,url
gh run view "$RECOVERY_RUN_ID" -R "$RELEASE_REPO" --log
gh api "repos/$RELEASE_REPO/issues/$ISSUE_NUMBER" --jq '{state,state_reason}'
gh issue view "$ISSUE_NUMBER" -R "$RELEASE_REPO" --json projectItems
```

Сверь фактический `Status` карточки проекта Scrumban (§3). Без подтверждённого
production success диагностируй исходный CD; не запускай recovery, не рисуй success
и не закрывай issue вручную. Recovery не делает deploy, повторный Health check
или course-sync. Отдельное поручение на merge не разрешает запуск CD.

Источники актуального контракта: [CONTRIBUTING](https://github.com/Cringe-Driven-Development-Team/.github/blob/main/CONTRIBUTING.md),
[CD](https://github.com/Cringe-Driven-Development-Team/frontend/blob/main/.github/workflows/cd.yml),
[reconcile-issues](https://github.com/Cringe-Driven-Development-Team/frontend/blob/main/.github/workflows/reconcile-issues.yml),
[проверка production](https://github.com/Cringe-Driven-Development-Team/frontend/blob/main/scripts/release/deployments.ts).
