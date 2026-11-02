# Справочник npm-publishing

Читай нужный раздел по состоянию из SKILL.md. Команды выполняются в проверенном
checkout frontend-packages, а не в каталоге плагина. Примеры используют shell;
переменные заполняй из текущих файлов и ответов сервисов.

## 1. Определить состояние

Пример для существующего каталога `packages/forms` (подставь найденный путь):

```bash
package_dir=packages/forms
package_name=$(jq -r .name "$package_dir/package.json")
package_version=$(jq -r .version "$package_dir/package.json")
repo=Cringe-Driven-Development-Team/frontend-packages
npm view "$package_name@$package_version" version --registry=https://registry.npmjs.org
npm view "$package_name" dist-tags --json --registry=https://registry.npmjs.org
gh run list --repo "$repo" --workflow release.yml --limit 10
```

У `npm view` учитывай код/причину: E401/сеть не означают отсутствующий пакет.
E404 сразу после publish тоже не доказывает отсутствие публикации. Не теряй
`@cdd-team/`: `router` и `@cdd-team/router` — разные имена.

Сопоставь package.json, `.release-please-manifest.json`, компонент в конфиге,
тег `<component>-v<version>`, GitHub Release, полный SHA и логи publish.
Изолируй работу от пользовательских изменений; обязательные проверки бери из
актуального AGENTS/runbook (Bun install/build/verify, интеграционные и остальные CI).
Прямой `bun scripts/publish-released.ts`, без `bun run`, сохраняет настоящий Node
для npm: в этом репозитории `bun run` может подменить Node.

## 2. Ручной bootstrap и baseline

Проверенный main, зелёный CI, собранные и проверенные архивы обязательны до
первой публикации. `npm whoami` проверяет локальный login, не OIDC workflow.
При необходимости запусти `npm login` с ожидающей 2FA-командой из раздела 4.
Публикуй из каталога пакета настоящим npm: `npm publish --access public`.
Зависимости должны быть доступны раньше зависимого пакета; порядок и проверки
выпуска уже есть в runbook/scripts, не создавай отдельный publisher.

После успешного exit 0 жди появления **точной версии**, включая правильный latest.
Временный `0.0.0-stage` — не повод повторять publish. Проверку ограничь текущим
окном ожидания runbook/скрипта; по его истечении сообщи неподтверждённый результат
и перечитай registry перед любым повтором.

Baseline создавай только для реально опубликованной версии на её исходном
проверенном SHA; не ставь тег на более новый main:

```bash
gh release create "$baseline_tag" --repo "$repo" --target "$published_sha" \
  --title "$baseline_tag" --notes "Baseline ручного bootstrap $package_name@$package_version"
```

Здесь `baseline_tag` берётся из component/version по конфигу, `published_sha` —
SHA публикации. Существующие теги не двигай и Releases не дублируй. При неизвестном
происхождении старой версии сначала установи его, не угадывай SHA.

Устаревший release PR, созданный до baseline, не сливай. Сверь его содержимое:
если он включает другие пакеты, сохрани их согласованные изменения и добейся
пересчёта текущей автоматики; не закрывай чужой выпуск только ради bootstrap.
Для PR только этого bootstrap устаревший вариант можно закрыть без merge.

## 3. Создать или исправить Trusted Publisher

Прочитай `npm trust --help`: CLI установленной версии должен поддерживать
подкоманды. Node/npm для OIDC: Node 22.14.0+, npm 11.5.1+; наличие именно
`npm trust` проверяется отдельно. При старом CLI используй актуальный npm в
изолированном окружении или доступный npm UI, не ослабляй авторизацию.

Чтение: `npm trust list "$package_name" --json`. Даже чтение может потребовать
2FA; для интерактивного подтверждения предпочти обычный вывод, см. раздел 4.
JSON `permissions: ["createPackage"]` соответствует **Allow npm publish**;
`createStagedPackage` — stage publish. Обычная публикация workflow требует первого.

Сверь repository с GitHub и package.json (не выводи owner из scope cdd-team).
При необходимости отзыва возьми ID конкретной проблемной записи из свежего
`list`, затем выполни `npm trust revoke "$package_name" --id "$trust_id"`.
Не отзывай рабочие записи других пакетов/провайдеров. Отсутствие expiry в выводе
не означает ни validated, ни expired: при совпадающих полях ищи статус доступным
API/UI и проверь лог обмена OIDC, не удаляй настройку вслепую из-за ENEEDAUTH.

Новая запись для текущего workflow:

```bash
npm trust github "$package_name" \
  --repository Cringe-Driven-Development-Team/frontend-packages \
  --file release.yml --allow-publish --yes
```

Environment опущен: release.yml его не использует. При изменении workflow
сверь значение заново. `--yes` отвечает на вопрос npm о создании доверия внутри
уже порученного подключения, не отменяет 2FA. Статус Pending validation после
создания ожидаем; в течение **2 дней от создания** нужен первый успешный
publish через эту запись. Ручной login-publish и выпуск соседнего пакета её не
подтверждают. Expired пересоздаётся; validated периодически не продлевается.

## 4. npm 2FA из среды агента

Запускай команду с TTY и сохрани session ID процесса. В среде с рабочим браузером
используй обычный npm browser flow. В headless Bash можно показать URL, сохранив
ожидание штатного npm flow, без установки глобального browser config:

```bash
BROWSER=echo npm trust list "$package_name" --no-progress
```

Передай полный URL **из этой команды** человеку, отправь ENTER в ожидающую
сессию, если CLI его просит, и продолжай читать процесс до завершения. Такой же
префикс применим к нужной trust/login/publish-команде. Из npm `--json` URL может
показываться замаскированным — не передавай `***` как ссылку.

Если страница 404: сравни URL посимвольно, включая последнюю цифру, с исходным;
проверь, не завершился/не истёк ли flow. Для истёкшего flow получи новую ссылку
повтором штатной команды. После «Authentication Successful» проверь exit code и
фактический результат исходного CLI. Не запускай несколько ожидающих 2FA для
одной операции и не обещай успех по одному браузерному скриншоту.

Пароли, OTP и токены человек вводит только на npm. Auth URL и результаты с
секретами не записывай в git/отчёты. Если браузер предлагает короткое окно без
повторной 2FA и человек его выбрал, используй его для уже порученных операций;
не рассчитывай, что `npm whoami` заменяет отдельную 2FA для trust.

## 5. Контрольный выпуск через release-please

Сначала проверь, нет ли готовой неопубликованной версии/упавшего publish —
тогда раздел 6, без нового bump. Если текущий bootstrap уже в registry, для
первой OIDC-публикации нужна следующая версия. Не жди неопределённого будущего fix.

Для нового пакета добавь полезное описание его публикации/разработки в собственный
README, например ссылку на runbook и команду проверки пакета. Сделай честный
`docs: описать выпуск <пакета>` с footer `Release-As: <следующий patch>`.
Footer — поддержанный механизм release-please; docs без footer в текущей Node
конфигурации сам по себе релиз не вызывает. Изменение должно лежать в каталоге
целевого пакета: в монорепозитории выбор идёт по путям, а не по scope коммита;
пустой commit в корне для выбора одного пакета ненадёжен.

`<следующий patch>` вычисли из реального baseline semver, а не копируй число из
примера. Версии, CHANGELOG и manifest обновляет release-please. Не меняй их руками,
не выдавай проверку издателя за исправление кода. Проведи docs PR и созданный
release PR с merge-коммитами, дождись CI на актуальном head, проверь отсутствие
конфликтов и итоговые версии/диапазоны зависимостей. Сохрани footer в самом
коммите; PR title/body не заменяют его при merge-коммитах.

Следуй правилам PR/merge репозитория; явное поручение на подключение покрывает
эти действия. Если доступен bypass и он разрешён инструкциями владельца,
используй его после проверки обязательных CI и актуального head. После merge
проверь post-merge workflow по SHA. Оставшуюся часть окна 48 часов используй для
проверки результата, не объявляй подключение завершённым на создании PR.

## 6. Частичный выпуск и проверка результата

`gh run view "$run_id" --repo "$repo" --json headSha,status,conclusion,jobs`
показывает попытку и job; лог failed job читай отдельно. Идентификаторы бери из
этого репозитория и нужного SHA. Исправь конкретную причину, затем повтори
существующий failed publish:

```bash
gh run rerun "$run_id" --failed --repo "$repo"
gh run watch "$run_id" --exit-status --repo "$repo"
```

В текущем workflow скрипт пропускает уже опубликованные версии, а путь
`not-attempted` после ошибки зависимости обрабатывает при повторе того же job.
Если повторять нужно один job, используй свежий job ID с `gh run rerun --job`.
`gh workflow run release.yml -f run_id=...` здесь повторяет **только notify**.
Ручной publish из checkout тега возможен по runbook для восстановления доступности,
но не доказывает достижение цели подключения к OIDC.

При ENEEDAUTH проверь сначала trust конкретного пакета и точные claims, затем
OIDC runner/permissions/версии Node/npm. В одном job React может пройти, а Router
упасть: общее окружение не подтверждает доверие всех пакетов. При совпадающих
полях и неизвестном статусе собери ответ обмена/диагностику; повторять без новых
данных или подставлять npm login-токен в workflow не следует.

`npm publish` exit 0 означает ожидание registry, не разрешение на повтор. Дай
встроенному подтверждению `publish-released.ts` завершиться; перечитывай точную
scoped-версию, если оно исчерпало попытки. После появления проверь:

```bash
npm view "$package_name@$package_version" version dist.attestations --json
npm view "$package_name" dist-tags --json
gh run view "$run_id" --repo "$repo" --json headSha,status,conclusion,jobs
```

Не принимай одно наличие `dist.attestations` за совпадение источника: прочитай
provenance по `dist.attestations.url`, сверь workflow и исходный SHA. Для публичных
пакетов из публичного репозитория OIDC включает provenance автоматически.
Финальный успех — registry/latest, OIDC publish, требуемые CI и notify завершены
успешно. Если пакет доступен, но notify ещё работает/упал, сообщи это отдельно и
восстанови уведомление, не перепубликуя пакет. Чистую установку не заявляй без
её фактической проверки.

## Первичные источники

- [Runbook frontend-packages](https://github.com/Cringe-Driven-Development-Team/frontend-packages/blob/main/docs/release-runbook.md)
- [release.yml](https://github.com/Cringe-Driven-Development-Team/frontend-packages/blob/main/.github/workflows/release.yml)
- [npm Trusted Publishers: настройка, 48 часов, OIDC/provenance](https://docs.npmjs.com/trusted-publishers/)
- [npm trust: list, revoke, github и флаги](https://docs.npmjs.com/cli/v11/commands/npm-trust/)
- [npm CLI: createPackage соответствует publish](https://github.com/npm/cli/blob/latest/lib/trust-cmd.js)
- [Release-As footer](https://github.com/googleapis/release-please#how-do-i-change-the-version-number)

Проверено 2026-11-03; перед операциями сверяй текущие документы и `--help`.
