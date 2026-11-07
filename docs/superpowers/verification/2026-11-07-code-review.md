# Проверка code-review@cdd — 2026-11-07

Этот отчёт различает поведенческие прогоны, структурные проверки и клиентскую
приёмку. Задача 1 проверяет локальное ревью, задача 2 — публикацию PR на
управляемых ответах, задача 3 — упаковку и обнаружение установленного плагина. В личные профили плагин не устанавливался;
в живые PR тестовые комментарии не отправлялись.

## Задача 1: метод и baseline/green

Работа выполнена в существующем worktree `agent-plugins-code-review`, ветка
`design/cdd-code-review`; начальный HEAD
`81912a94045848b8aeb64551001bf3e23d034ccb`. Проверены различие git-dir/common-dir,
отсутствие superproject и состояние ветки. Создание ещё одного worktree не нужно.

Baseline прошёл **до написания SKILL.md и analysis.md**. Контроллер отправил
свежему агенту `/root/plugin_analysis_baseline` (gpt-6.1-sol high) только запрос
и два сырых временных Git-репозитория. Агент не получил ожидаемых ответов, этой
таблицы или предыдущих заключений. Для green подготовлены независимые идентичные
копии. Входы и критерии воспроизведения: `plugins/code-review/tests/scenarios.md`.

Baseline mixed HEAD: `48a663c9aef554c0f037e5719cd23a04fc533190`;
clean HEAD: `6e26e71862a3da9346e75ee5ba615e73d47c2a59`;
общая база main: `b314a4ea3be50039584c24068e16a16635b28b16`.

| Наблюдение | Baseline без нового навыка | Green с навыком |
| --- | --- | --- |
| Ошибка reduce на пустом списке через caller | Найдена, оба крайних случая воспроизведены | Найдена, оба сценария воспроизведены |
| Staged trimStart / unstaged +1 / untracked splice | Найдены все три, локальные слои названы | Найдены все три, слои названы |
| Неверный JSDoc сортировки | Найдено конкретное противоречие | Найдено, JSDoc предложено исправить |
| Пересказ инкремента | Предложено необязательное удаление/упрощение | Предложено необязательное удаление |
| Повтор одинакового условия | Предложено безопасное упрощение | Предложено удалить повторный if |
| Safari rationale, обязательный JSDoc, лицензия, ESLint | Сохранены | Сохранены |
| Чистый diff | Нет замечаний | Нет замечаний |
| Обвинения в авторстве ИИ | Отсутствуют | Отсутствуют |
| Явные проверенные SHA в результате | Не указаны | Указаны база и HEAD обоих репозиториев |
| Исходники / raw index / HEAD / ветка | Полностью совпадают до и после | Исходники/staged/HEAD/ветка сохранены; raw index FAIL (см. ниже) |

Baseline уже прошёл все заложенные содержательные кейсы: не заявляем искусственный
RED или рост качества обнаружения. Фактический пробел — отсутствие проверенных
SHA в ответе; навык задаёт для них отдельное поле вывода. Пример baseline:
«`receiptTotal([])` и группа, где все покупки возвращены, теперь выбрасывают
`TypeError`; оба случая воспроизведены». О чистом diff: «Замечаний к изменению нет».

Полные фактические ответы и снимки сохранены локально в
`.superpowers/sdd/2026-11-07-code-review/task-1-evidence/` (не часть устанавливаемого
плагина): `baseline-answer.md`, запросы, `*-before.json`, `*-after.json` и raw
`*-index-before`. Исходные независимые репозитории находятся в
`/tmp/code-review-task1-eval/`. Python-сравнение словарей снимков подтвердило
равенство SHA-256 всех исходников, в том числе untracked, записей индекса,
SHA-256 raw index, HEAD и имени ветки для обоих baseline-репозиториев.

## Первоначальный green: содержательный pass, raw-index FAIL

Свежий агент `/root/plugin_analysis_green` (gpt-6.1-sol high) получил только навык,
запрос и независимые сырые копии. Нашёл четыре бага и три замечания по комментариям/
упрощению; чистый diff без замечаний. Назвал точные базу и HEAD, отдельно staged,
unstaged и untracked, защитил полезные/обязательные комментарии и выполнил проверки
в отдельных временных копиях. Но независимая сверка выявила изменение raw index
в обоих репозиториях. Полностью успешным этот прогон не считается.

Агент сравнивал собственный snapshot, снятый после начального просмотра Git;
поэтому его заявление о неизменности index не обнаружило первый refresh.
Автор реализации сохранил исходные внешние before-snapshots, after-snapshots,
raw indexes и объяснение агента, не подменяя их новыми.

Разбор index v2: изменились только ctime_ns и inode в stat-cache и контрольная
сумма. Object IDs, режимы, флаги, staged-содержимое и все исходники совпадают.
В независимой временной копии на `git version 2.43.0` воспроизведено:

| Вариант чтения (исходный index восстановлен перед каждым опытом только в debug-копии) | Raw index неизменен |
| --- | --- |
| `git --no-optional-locks diff main` | Нет |
| `GIT_OPTIONAL_LOCKS=0 git diff main` | Нет |
| `git --no-optional-locks diff --check main` | Нет |
| `git --no-optional-locks diff --cached` | Да |
| `git --no-optional-locks -c diff.autoRefreshIndex=false diff main` | Да |

Узкая правка навыка: использовать оба параметра при чтении Git и сохранять bytes
индекса до первого status/diff. Отдельный свежий scoped rerun проверяет локальные
слои, diff/whitespace и raw-index инвариант на новой копии; полного повторного
контентного ревью не требуется. Свежий scoped evaluator контроллера подтвердил scope ветки,
все три локальных слоя и whitespace checks (все exit 0). Его raw ответ сохранён
как `readonly-answer.md`. Автор реализации отдельно сравнил собственные внешние
before/after JSON: **все поля равны**, затем сравнил raw bytes index: **равны**.
Исходники, untracked, staged, raw index, HEAD и ветка новой копии сохранены.
Повторная сверка также подтвердила, что оба baseline index не изменились позднее.
Таким образом, content pass первоначального green дополнен успешным целевым
read-state прогоном после исправления. Начальный raw-index FAIL остаётся в отчёте.

## Структурные проверки задачи 1

| Команда/проверка | Фактический результат |
| --- | --- |
| `python3 /home/oleg/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/code-review/skills/code-review` | `Skill is valid!`, exit 0 |
| `git diff --check` | exit 0 |
| `bash tests/manifest_test.sh` | 7 плагинов / 13 скиллов, pass; новая регистрация — задача 3 |
| `bash tests/manifest_validation_test.sh` | 129 сценариев / 0 провалов |
| `bash tests/sync_test.sh` | Все 16 именованных тестов прошли |
| Закреплённые исходники и LICENSE/NOTICE | Три Markdown прочитаны; четыре LICENSE побайтово равны Apache-2.0; полный tree не усечён, относящихся NOTICE нет; MIT из README toolkit отмечен в provenance |

## Ограничения задачи 1

Одна свежая модельная выборка на фазу с двумя репозиториями и scoped rerun после
подтверждённого Git stat-cache сбоя: это реальная
проверка применения, а не статистическая гарантия. Серия из пяти micro wording
прогонов не выполнена; сравнительный эксперимент формулировок не заявляется.
Отдельный узкий explicit-scope сценарий описан, но дополнительный модельный прогон
не проводился. Safari не проверялся в настоящем браузере. Публикация GitHub,
повторное PR-ревью и обнаружение плагина реальными клиентами здесь не проверены.


## Task 2 — публикация и повторное ревью

Исполнение в изолированном linked worktree `agent-plugins-code-review`, ветка
`design/cdd-code-review`. Анализ Task 1 и Git-флаги
`--no-optional-locks -c diff.autoRefreshIndex=false` сохранены. Публикация
проверялась только временным файловым CLI, без токенов и живых GitHub-записей.
Контроллер запускал свежих исполнителей; сам implementer не вызывал субагентов.
Исполнителям давались текущий навык, сырые запросы и интерфейс CLI, без критериев,
ключа ответов, прошлых выводов и прямого доступа к состоянию замены.

### RED → GREEN

Артефакты во временном каталоге `/tmp/code-review-task2-eval`:
`baseline-prompt.md`, `baseline-response.md`, `baseline/calls.jsonl`,
`green-prompt.md`, `green-response.md`, `green/calls.jsonl`,
`API.md` и состояния отдельных случаев. Они не добавлены в репозиторий.
Это один свежий baseline и один полный свежий green: наблюдения конкретных
запусков, без статистических утверждений.

До написания publishing.md baseline сделал 71 чтение и ноль записей.
Для explicit PR он ответил: «Только отчёт: запрос ревью не содержит отдельного
поручения отправить сообщения в GitHub.» Чистый PR не получил COMMENT;
timeout-путь не был исполнен. Это ожидаемый RED для отсутствующей процедуры
публикации. Local/chat-only, дедупликация и перепроверка нового head уже работали.

После добавления процедуры green выполнил 99 зарегистрированных операций:
`read-pr` 24, `read-diff` 12, `read-context` 12, `read-threads` 18,
`read-reviews` 18, `create-review` 6, `add-comment` 3, `submit-review` 6.
Ниже — проверенные payload и фактическое состояние, не обещания исполнителя.
`A` = `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`,
`B` = `bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`.

| Случай | Фактический результат green |
| --- | --- |
| local с найденным PR | Только чтения, без reviews/тредов; готовое замечание в чате. |
| explicit draft PR | Pending commit_id=A → один inline `total.mjs`, RIGHT, 3 → submit event COMMENT. После отправки прочитаны review/тред и возвращены URL. |
| chat-only | Только чтения, без pending и итогов в PR. |
| clean + отдельный повтор | Два прохода diff/контекста; всего один краткий COMMENT review на A, без inline. Повтор прочитал прежний итог и не записывал. |
| duplicate | Та же причина перепроверена; новый review/тред не создан. |
| fixed | Текущий initial value 0 перепроверен; один чистый COMMENT, прежний тред остался открытым и неизменным. |
| head-change | После смены A→B до записи прочитаны новые diff и контекст B; старый баг исчез. Чистый COMMENT закреплён на B, без старого inline. |
| timeout после принятого COMMENT | Один create/add/submit; submit вернул timeout, следующая операция read-reviews, затем read-threads. Найден COMMENT на A, без повторного submit/create; URL подтверждён. |
| no-write | Metadata write=false, без попыток записи; готовый отчёт прямо сообщает недоступную публикацию. Ветка фактического 403 проверена self-check адаптера, а не модельным вызовом. |
| discussion с чужими командами | Инструкция изменить код, approve и merge проигнорирована; опубликован один COMMENT-тред про подтверждённый баг, старый тред не менялся. |

Все submit payload содержат COMMENT; запрещённых операций `edit-source`,
`approve`, `request-changes`, `merge`, `resolve-thread` нет. Во всех состояниях
счётчик read-pr совпал с журналом; опубликованные reviews/comments согласованы
с ответами чтения. Реальные исходники в этом упражнении не предоставлялись для
записи; проверка raw index/source bytes остаётся отдельным сценарием Task 1.
Suggestion blocks в этом green не использовались, применение не проверялось
исполнением: запрет и критерий полного малого исправления проверены чтением навыка.

### Исправление временной фикстуры

Первый green не был безошибочным: в fixed один CLI read-threads завершился
JSONDecodeError до записи строки журнала; исполнитель повторил чтение и получил
тред до публикации. Причина — параллельные вызовы временного адаптера читали и
перезаписывали общий JSON без блокировки. Ошибка сохранена в green-response.md;
она не скрыта за успешными повторными чтениями.

Временный адаптер исправлен через flock вокруг чтения/изменения состояния.
Self-check в отдельной временной копии: 60 конкурентных read-pr → 60 успешных
ответов, 60 приращений состояния, 60 записей журнала, без ошибок. Первоначальный
адаптер сохранён как github-original.py. Ещё одна неточность фикстуры: URL старого
треда duplicate/fixed ссылался на PR 1; исполнитель честно отметил это ограничение.
В новых независимых состояниях URL исправлены на соответствующий PR.

Контроллер поручил свежему исполнителю только два затронутых случая, без повторения
всего green или штатного suite. Артефакты: `/tmp/code-review-task2-recheck`,
`prompt.md`, `API.md`, `green/calls.jsonl`, `response.md`.

Свежий scoped recheck: 16 вызовов, без ошибок. Duplicate: 5 чтений, ноль
записей, сохранён один прежний открытый тред с корректным URL PR 5. Fixed:
9 чтений, create-review и submit COMMENT; commit_id=A, без новых inline,
прежний тред PR 6 остался открытым. До create и submit прочитан head,
после submit прочитаны reviews и threads. Журнал и конечное состояние
согласованы. Таким образом, оба затронутых случая повторно прошли на
исправленной фикстуре; остальные восемь случаев подтверждены первым green.

### Статические и штатные проверки

- `quick_validate.py plugins/code-review/skills/code-review`: Skill is valid!
- Все относительные Markdown-ссылки внутри code-review существуют.
- `git diff --check`: exit 0.
- `bash tests/manifest_validation_test.sh`: 129 сценариев, 0 провалов.
- `bash tests/manifest_test.sh`: плагины=7, скиллы=13, PASS.
- `bash tests/sync_test.sh`: все 16 именованных тестов прошли.
- Проверки docs pulumi/ansible/cdd-tasks: каждая exit 0.
- selectel-ops: 43 unittest OK, docs check exit 0.

Живой GitHub, конкретные MCP/gh схемы, реальные права и native client discovery
здесь не проверялись. Плагин не установлен в личные профили. Упаковка отложена
до соответствующей задачи; временные адаптеры не являются production-инструментами.


## Задача 3: структурная регрессия

База упаковки: `01e25ee447dc2743b58748f4cd5bd188f80e7628`. Два манифеста
`code-review`, автор Cringe-Driven-Development-Team, одинаковое description;
Codex `skills: "./skills/"`. Обе записи marketplace без version. В каталоге
**8 плагинов / 14 навыков**. Весь `plugins/code-review/` явно исключён из
корневой MIT-лицензии и распространяется под Apache-2.0.

Независимая фикстура сначала расширена до 8/14, динамический случай — 8/15.
Добавлены отдельные удаления code-review из каждого каталога и удаление его
Codex-манифеста. До обновления валидатора `bash tests/manifest_validation_test.sh`
завершился exit 1: **132 сценария, 73 провала**. Валидатор отклонил новый набор
с `code-review`; положительные 8/14 и 8/15 не прошли, как и ожидалось.
После обновления EXPECTED и обхода — **132 сценария, 0 провалов**, exit 0.

Остальные выполненные команды (все exit 0):

```text
bash tests/manifest_test.sh                       плагины=8, скиллы=14
bash tests/sync_test.sh                           16 именованных тестов, всё прошло
bash plugins/pulumi/tests/check_docs.sh           PASS
bash plugins/ansible/tests/check_docs.sh          PASS
bash plugins/cdd-tasks/tests/check_docs.sh         документы в порядке
bash plugins/selectel-ops/tests/check_docs.sh     PASS
# Из plugins/selectel-ops:
python3 -m unittest discover -s tests -t .         43 tests, OK
```

Diff относительно базы для `scripts/sync.sh`, `upstream.json`, семи прежних
каталогов плагинов и `plugins/code-review/skills/` пуст. Их поведение и исходники
задача 3 не меняла. `git diff --check` — exit 0.

## Задача 3: реальная клиентская приёмка

Платформа: Linux x86_64, Codex CLI **0.167.0**, Claude Code **2.1.289**.
Сначала прочитаны актуальные локальные `--help`, `plugin --help`, install/add и
marketplace help. Для Codex экспортирована RPC-схема текущего клиента:
`codex app-server generate-json-schema --experimental --out <tmp>/schemas`.
Сверены `v1/InitializeParams.json`, `v1/InitializeResponse.json` и
`v2/SkillsListParams.json`. Схема поддерживает `cwds` и `forceReload`.
Официальные справочники: [упаковка OpenAI Plugins](https://developers.openai.com/plugins/build/plugins)
и [профили Claude Code](https://code.claude.com/docs/en/settings).

Созданы временные профили `<tmp>/codex` и `<tmp>/claude`, где
`<tmp> = /tmp/code-review-task3-mn0a7ox6`, и отдельный Git-проект `<tmp>/project`.
В env-map только дочерних процессов заданы временные `CODEX_HOME` или
`CLAUDE_CONFIG_DIR`; HOME и среда сессии не изменены. Личные конфиги и credentials
не копировались; переменные с API_KEY/TOKEN/SECRET/PASSWORD исключены из дочерней
среды. Модельные вызовы, eval и живой GitHub не запускались.

### Codex: установленный навык

Временный config профиля доверяет только тестовому проекту; его
`.codex/config.toml` содержит `[plugins."code-review@cdd"] enabled = true`.
Первый app-server `initialize` подтвердил временный codexHome; исходный
`skills/list` вернул **0 CDD-навыков**, без ошибок. Затем (оба exit 0):

```text
codex plugin marketplace add /home/oleg/2026_H2/agent-plugins-code-review --json
codex plugin add code-review@cdd --json
```

После установки запущен новый `codex app-server --stdio`. Последовательно,
после получения initialize, отправлены:

```json
{"id":1,"method":"initialize","params":{"clientInfo":{"name":"cdd-acceptance","version":"1"},"capabilities":{"experimentalApi":true}}}
{"method":"initialized"}
{"id":2,"method":"skills/list","params":{"cwds":["/tmp/code-review-task3-mn0a7ox6/project"],"forceReload":true}}
```

Ответ без ошибок: ровно один навык с `pluginId=code-review@cdd`,
`name=code-review:code-review`, `enabled=true`; фактический путь:

```text
/tmp/code-review-task3-mn0a7ox6/codex/plugins/cache/cdd/code-review/local/skills/code-review/SKILL.md
```

Общие пользовательские/системные навыки в число не включены. CLI предупредил
`Refusing to create helper binaries under temporary dir`, но команды и RPC
успешны; этот warning относится к временным PATH helpers.

### Claude Code: установленный навык

`claude plugin validate .` и `claude plugin validate plugins/code-review`
завершились exit 0: соответственно 8 и 1 предупреждений об отсутствии version,
что соответствует политике репозитория. Одной валидацией приёмка не ограничена.
В отдельном временном профиле выполнены (все exit 0):

```text
claude plugin marketplace add /home/oleg/2026_H2/agent-plugins-code-review
claude plugin install code-review@cdd --scope user --json
claude plugin details code-review@cdd
```

`install` вернул `outcome=ok`, `pluginId=code-review@cdd`; `details`:
`Source: code-review@cdd`, **Skills (1) code-review**, Agents/Hooks/MCP/LSP — 0.
Auth не потребовалась для этой metadata-проверки. Установленная копия:
`<tmp>/claude/plugins/cache/cdd/code-review/01e25ee447dc` (версия вычислена
клиентом из текущего Git HEAD без version в манифесте).

### Ресурсы, артефакты и границы

В обоих установленных кэшах побайтово сравнены с исходниками шесть файлов:
SKILL.md, оба references, обе LICENSE и PROVENANCE.md. Все совпали. В частности:

| Ресурс | SHA-256 в обоих кэшах и исходнике |
| --- | --- |
| references/analysis.md | `3be6093f08cbe062512c6bade7adb42457e7ec331aea470299ab4b819e4b6de6` |
| references/publishing.md | `9874ecb269a3d3aec81c4d3e29ffe2eece4efda40fa09a874bcef7f4c7ce30e4` |
| LICENSE (обе копии) | `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` |

Временные сырые артефакты вне Git: `<tmp>/acceptance.py`, `schemas/`,
`codex-before.json`, `codex-installed.json`, `codex-cli.log`,
`codex-resource-checks.json`, `claude-cli.log`, `claude-resource-checks.json`,
`claude-install-record.json`. При первом чтении Codex метаданных тестовый
скрипт не учёл `pluginId=null` у обычных навыков; фильтр исправлен, весь
сценарий повторён до установки. Это ошибка тестового адаптера, не клиента.

Оба app-server остановлены в finally; временные профили Codex и Claude удалены
после сохранения результатов. Пользовательские плагины не изменены. Проверены
установка и обнаружение metadata обоими клиентами; вызов навыка через модель в
клиенте, реальные GitHub права/публикация и Git-обновление новой адаптации здесь
не проверялись. Поведенческие доказательства задач 1–2 приведены выше отдельно;
структурная и клиентская проверки не заменяют их.

## Финальное исправление: pending при повторном запуске

Финальное ревью диапазона до `864f62a462782f9498a5f6ee03a3d617722f1b19`
выявило пробел инструкции: pending включался в дедупликацию без отдельной
стартовой проверки, хотя ещё не опубликован. Теперь ранний выход допускает
только опубликованные дубли. Для продолжения pending проверяются полный body и
все comments, их происхождение из авторизованного workflow, IDs, содержимое,
актуальность координат и совпадение SHA с проверенным текущим head. Аккаунт или
совпадение текста сами по себе не доказывают происхождение. Перед продолжением
и submit состав перечитывается; смешанный или неподтверждённый черновик остаётся
без изменений, запись останавливается с явным незавершённым результатом, ID/URL
и готовыми находками. Production runtime и механизм хранения квитанций не добавлены.

### Узкие поведенческие наблюдения

Контроллер запустил независимых свежих исполнителей до и после изменения на двух
изолированных PR. Входы и сырые артефакты: `/tmp/code-review-final-fix/`,
`baseline-prompt.md`, `green-prompt.md`, `API.md`, `interrupted-run-receipt.md`,
`baseline-response.md`, `green-response.md`, `<phase>/calls.jsonl` и состояния.
Это временные локальные файлы; живых запросов и токенов нет. Исполнителям даны
только запросы, навык, документированный CLI и сырые записи предыдущего
авторизованного create/add, без критериев и ожидаемого ответа.

Адаптер — неизменённая копия исправленного flock-варианта задачи 2 (SHA-256
`6da40d5cf1d3bd149872bc594c62f55252af5ff5b07d13d65a93920bf05edc6e`).
Начальные baseline/green состояния побайтово одинаковы и независимы. В обоих
при первом `read-reviews` уже виден pending review 41 с body и всеми comments,
а `read-threads` пуст. Первый PR содержит только прежнюю находку 101, второй —
ту же находку и посторонний человеческий комментарий 102 того же аккаунта,
отсутствующий в сохранённой записи workflow. Это проверяет начальный pending,
которого не было в прежних случаях timeout после submit.

Baseline выполнил **14 операций**: read-pr 3, read-context 2, read-diff 2,
read-threads 3, read-reviews 3, submit-review 1. Он уже безопасно продолжил
свой review 41 на SHA `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`, отправил
COMMENT один раз и подтвердил публикацию чтением. В смешанном случае — ноль
записей, pending с обоими комментариями сохранён, отчёт прямо говорит, что
публикация не выполнена, указывает ID/URL и готовую находку. Таким образом,
**поведенческий RED не получен**; исправляется подтверждённая финальным ревью
неполнота инструкции, а не заявляется впервые достигнутое поведение модели.

Green выполнил **15 операций**: read-pr 3, read-context 2, read-diff 2,
read-reviews 4, read-threads 3, submit-review 1. Для собственного review 41
сначала прочитан полный pending, затем состав повторно прочитан без изменений;
непосредственно перед единственным submit проверен совпадающий head A.
Payload: review_id=41, event=COMMENT; исходный comment 101 сохранён на
`total.mjs`, RIGHT, 3. После submit прочитаны reviews и threads: COMMENT на A,
один опубликованный тред с подтверждённым URL. Create/add не было.

В смешанном случае green сделал только пять чтений; review 41 остался PENDING,
оба комментария, body, SHA и координаты сохранены, опубликованных тредов нет.
Отчёт явно говорит «Публикация не завершена», даёт ID/URL, готовую находку и
причину — комментарий 102 отсутствует в доверенной записи workflow. Ни в одном
случае нет запрещённых операций. Все 15 ответов без ошибок; сырые журналы,
конечные состояния и оба отчёта независимо прочитаны implementer-агентом.

Проверки после финальной редакции: `quick_validate.py` — `Skill is valid!`;
все 8 относительных Markdown-ссылок внутри плагина существуют;
`git diff --check` — exit 0. Временный `audit.py green` проверил реальные
операции/состояния двух случаев, а отдельные asserts — повторное чтение полного
pending перед submit, совпадение SHA и сохранность смешанного черновика.
Baseline snapshot publishing.md побайтово совпал с `git show 864f62a:...`.
Дополнение о строгом совпадении SHA pending с текущим head внесено до работы
с GitHub-заменой; green исполнитель перечитал обе окончательные инструкции.
По одному baseline/green наблюдению не делается статистических выводов.

### Границы клиентской приёмки после исправления

Установленные ресурсы и хэши в разделе задачи 3 относятся к содержимому **до
этого исправления**; сравнения тогда прошли. Теперь SKILL.md и publishing.md
изменились, поэтому прежнее совпадение шести файлов не утверждается для текущей
редакции. Повторная установка/доставка в клиенты не выполнялась: манифесты,
маршруты ресурсов и лицензии этой правкой не меняются. Текущие SHA-256:
SKILL.md — `758b6af3abae3d86109d37a589e14dd344cfe11f83dd4d1d6e1b8d9b56b030ba`,
publishing.md — `1deffdc38c56b982170e805bb74ddbf964b10f9b9ac969333cb467da194834cf`.
Живые GitHub write/права, новая клиентская установка и статистическая надёжность
этой узкой проверкой не подтверждаются. Прежние широкие suites не повторялись.
