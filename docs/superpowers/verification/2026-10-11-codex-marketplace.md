# Приёмка маркетплейса CDD в Codex — 2026-10-11

Проверенный клиент: `codex-cli 0.162.1`, macOS arm64. Исходная упаковка:
`c8d8d4d`. Проверка обращалась к CLI и app-server без вызовов модели.

## Окружение и исходное состояние

Созданы отдельные временные профили клиента и проекты. В env-map каждого
дочернего Codex задавался временный `CODEX_HOME`; текущая среда агента и
личный профиль не менялись. Итоговые сценарии выполнялись без переопределения
`HOME`. Личные конфиги и учётные данные не копировались. Общие пользовательские
навыки, которые клиент читает из `~/.agents/skills`, исключены из подсчёта CDD.

Схемы экспортированы целевым CLI:

```bash
codex --version
codex app-server generate-json-schema --experimental --out <временный-каталог-схем>
```

Через `codex app-server --stdio` последовательно отправлены запросы ниже;
между первым и следующими сообщениями получен ответ на `initialize`:

```json
{"id":1,"method":"initialize","params":{"clientInfo":{"name":"cdd-acceptance","version":"1"},"capabilities":{"experimentalApi":true}}}
{"method":"initialized"}
{"id":2,"method":"skills/list","params":{"cwds":["<абсолютный-путь-тестового-проекта>"],"forceReload":true}}
```

До любой установки проверен `initialize.codexHome`:
`/private/tmp/cdd-codex-acceptance-20261011/local/codex`. Исходное число
навыков из установленного CDD-кэша — **0**; ошибок `skills/list` нет.

## Локальная установка и обнаружение

Репозиторий скопирован из `git archive HEAD` в каталог с пробелами. Реально
выполнены команды (все exit 0):

```bash
codex plugin marketplace add '/private/tmp/cdd-codex-acceptance-20261011/local/marketplace copy with spaces'
codex plugin marketplace list
codex plugin list
codex plugin add pulumi@cdd
codex plugin add ansible@cdd
codex plugin add selectel-ops@cdd
codex plugin add cdd-tasks@cdd
```

CLI распознал каталог `cdd` и четыре плагина с отсутствующим `version`.
Доверие тестовому проекту задано в конфиге временного профиля, а в проектном
`.codex/config.toml` записаны четыре секции:

```toml
[plugins."pulumi@cdd"]
enabled = true
[plugins."ansible@cdd"]
enabled = true
[plugins."selectel-ops@cdd"]
enabled = true
[plugins."cdd-tasks@cdd"]
enabled = true
```

После установки новый app-server выполнил `initialize`, `initialized` и
`skills/list` с `forceReload: true`. Обнаружены **4 плагина / 10 навыков**:

| pluginId | Число | Имена навыков без префикса |
|---|---:|---|
| `pulumi@cdd` | 6 | `pulumi-best-practices`, `pulumi-component`, `pulumi-debug-failed-operation`, `provider-upgrade`, `pulumi-cli`, `pulumi-typescript` |
| `ansible@cdd` | 2 | `ansible-good-practices`, `ansible-org` |
| `selectel-ops@cdd` | 1 | `selectel-ops` |
| `cdd-tasks@cdd` | 1 | `cdd-tasks` |

Множество имён совпало с каталогом спецификации. Клиент отдаёт имена
`<плагин>:<имя>` и соответствующий `pluginId`; у всех `enabled=true`.
Каждый фактический путь имеет вид:

```text
/private/tmp/cdd-codex-acceptance-20261011/local/codex/plugins/cache/cdd/<плагин>/local/skills/<имя>/SKILL.md
```

Проверены все 10 путей: они принадлежат установленному кэшу, а не исходной
копии. Системные и общие пользовательские навыки не включены в число 10.

## Вложенные ресурсы

Сравнены инвентарь путей и байты всех `SKILL.md`, `references/` и `scripts/`
в четырёх установленных плагинах: **29 уникальных файлов**, все совпали.
Обязательные ресурсы доступны непосредственно в установленной копии:

| Путь относительно `plugins/cache/cdd/` | SHA-256 источника и установленного файла |
|---|---|
| `ansible/local/references/coding_style.adoc` | `e2ad83319433e33d05d3622a27e37a01033a995df1b0f349dafe8940f713110e` |
| `pulumi/local/skills/pulumi-cli/references/pulumi-cli-commands.md` | `a41c3c1423ef242ccb97aabebcb93961ac43a8625064cc9a0ac704fd6fdc4e7a` |
| `selectel-ops/local/skills/selectel-ops/scripts/selectel.py` | `c9d96d137b429e2f3c36d2028a83535ed2be991b7161724e5d691779c23ef73f` |

Скрипт Selectel при проверке ресурсов не выполнялся.

## Git-обновление A → B

Отдельный чистый профиль:
`/private/tmp/cdd-codex-acceptance-20261011/git/codex`; до установки новый
`initialize` подтвердил этот `codexHome`, `skills/list` дал 0 CDD-навыков.
Текущая упаковка скопирована во временный Git-источник, создан bare-репозиторий
и опубликован через собственный `python3 -m http.server` на loopback.
До каждого получения ревизии клиентом выполнен `git update-server-info`.
Публичный GitHub в этом сценарии не запрашивался.

| Ревизия | Git SHA | Изменение тестового источника |
|---|---|---|
| A | `5deeac98189a75bdee9e3e3f2f61592748402fc0` | В справочник `pulumi-cli` добавлена строка `cdd-codex-probe-v1` |
| B | `4ce0c8d903987710261109771ca384bf2b1b8a07` | Строка заменена на `cdd-codex-probe-v2`; добавлен `plugins/pulumi/skills/codex-probe/SKILL.md` |

Frontmatter временного навыка: `name: codex-probe`,
`description: Temporary Codex installation probe`. Между A и B изменены
ровно эти два файла; имя плагина, `version` и манифест не менялись.
Команды клиента (все exit 0):

```bash
codex plugin marketplace add http://127.0.0.1:53876/marketplace.git
codex plugin add pulumi@cdd
# После публикации ревизии B и повторного git update-server-info:
codex plugin marketplace upgrade cdd
```

В ревизии A установленный справочник содержал `cdd-codex-probe-v1`,
свежий `skills/list` обнаружил **6** Pulumi-навыков. Сразу после `upgrade`
установленный справочник содержал B и не содержал A; его байты совпали
с источником B. Повторный `plugin add` **не потребовался**.

После перезапуска app-server свежий `skills/list` обнаружил **7**
Pulumi-навыков, все `enabled=true`, `pluginId=pulumi@cdd`. Новый навык:

```text
name: pulumi:codex-probe
path: /private/tmp/cdd-codex-acceptance-20261011/git/codex/plugins/cache/cdd/pulumi/local/skills/codex-probe/SKILL.md
```

Оба контрольных изменения существуют только во временном тестовом источнике.
Собственный HTTP-процесс остановлен в `finally`.

## Условия выполнения и доказательства

Сырые ответы CLI/RPC, экспорт схем, списки ресурсов и регрессия сохранены
в `/private/tmp/cdd-codex-acceptance-20261011/`: `before-no-home-override-rpc.json`,
`installed-rpc.json`, `all-resource-checks.json`, `git-A-rpc.json`,
`git-B-rpc.json`, `git-after-upgrade.json`, `git-result.json`, `regression.json`.
Эти временные артефакты не входят в репозиторий; их содержимое представлено
выше именами, числами, путями, хэшами и фактическими результатами.

Песочница запретила первоначальный `bind` loopback HTTP (EPERM).
Git-сценарий завершён при согласованном запуске вне песочницы. CLI выдавал
предупреждение `Refusing to create helper binaries under temporary dir`;
команды завершились с exit 0, RPC не сообщил ошибок. Личный профиль не менялся.

## Регрессия

Все команды выполнены последовательно с exit 0:

```text
bash tests/manifest_validation_test.sh              125 сценариев, 0 провалов
bash tests/manifest_test.sh                         плагины=4, скиллы=10
bash tests/sync_test.sh                             16 сценариев, всё прошло
bash plugins/pulumi/tests/check_docs.sh             прошло
bash plugins/ansible/tests/check_docs.sh            прошло
bash plugins/cdd-tasks/tests/check_docs.sh          прошло
bash plugins/selectel-ops/tests/check_docs.sh       прошло
```

Из `plugins/selectel-ops/`: `python3 -m unittest discover -s tests -t .` —
38 тестов, `OK`. Проверка исходников относительно `b745231` дала пустой diff
для `.claude-plugin`, манифестов Claude Code, навыков, references, лицензий,
`upstream.json` и `scripts/sync.sh`. `git diff --check` — exit 0,
без диагностики.

## Повторение клиентской проверки

В новом временном профиле экспортируйте схемы установленного CLI, запустите
app-server и подтвердите временный `initialize.codexHome` до установки.
Получите исходный `skills/list`, затем зарегистрируйте каталог, установите
выбранные плагины и включите их в доверенном проекте. Перезапустите
app-server и получите свежий `skills/list`; сопоставьте имена, `pluginId`,
`enabled` и пути установленного кэша с таблицей выше. Для полной приёмки
повторите сравнение ресурсов и Git-сценарий обновления.
