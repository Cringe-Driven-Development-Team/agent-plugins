# Проверка frontend-packages / npm-publishing

Дата: 2026-11-03. Реализация по утверждённой
[спецификации](../specs/2026-11-03-frontend-packages-npm-publishing-design.md) и
[плану](../plans/2026-11-03-frontend-packages-npm-publishing.md).

## Метод

Четыре сценария в `plugins/frontend-packages/evals/`, один независимый агент на
сценарий без скилла (baseline) и другой свежий агент с SKILL.md/REFERENCE.md (GREEN).
Все восемь агентов запущены с `fork_turns=none`: не получают эту беседу, спеку,
план, graders или заключения автора. Оцениваются решения и конкретные команды,
а не наличие фраз в Markdown. Проверяющий автор прочитал ответы полностью и
сопоставил их с graders.

Только чтение, смоделированные данные; npm/GitHub-операции не выполнялись.
Для GREEN отдельно уточнено, что read-only cat/sed разрешены как механизм чтения:
в этом harness нет отдельного Read, запрет команд означает операционные действия.
Это уточнение не содержит решений сценариев. Вызовы `claude plugin eval` из README
не запускались; результаты ниже — прогоны через доступный инструмент subagent.

Это проверка техники и справочника с решениями по наблюдаемому состоянию, а не
микротестирование формы ответа; повторные серии из пяти выборок не проводились.

## Baseline: наблюдавшиеся пробелы

| Сценарий / агент | Результат | Существенное наблюдение |
| --- | --- | --- |
| bootstrap / baseline_bootstrap | Пробел | Отложил завершение до будущего содержательного изменения; нет конкретного контрольного patch и срока 48 часов |
| trust-recovery / baseline_trust | Пробел | Не знает действующих команд изменения trust и трактует createPackage как сомнительное право публикации |
| partial-release / baseline_partial | Ошибка | Проверяет другой, unscoped router в npm |
| diagnostic-only / baseline_diagnostic | Граница поручения соблюдена, фактический пробел | Не изменяет настройки, но снова сомневается в publish-разрешении createPackage |

Дословные выдержки исходных ответов:

- **bootstrap:** «Если нового содержательного изменения нет, подключение
  подготовлено, но автоматический выпуск пока не проверен; выдумывать изменение
  ради версии не нужно». Остальное решение включало bootstrap, baseline,
  сохранение версий и проверку OIDC; состояние B корректно признано завершённым.
  Скилл добавляет конкретный честный docs-коммит с Release-As в каталоге пакета.
- **trust-recovery:** «Точные команды изменения trust следует взять из справки
  установленного npm; по данным сценария нельзя достоверно восстановить их
  синтаксис». И: «наличие только этого разрешения нельзя считать доказательством
  права публиковать новые версии уже существующих пакетов». При этом typo/expiry,
  сохранение React, ожидание CLI и отсутствие нового bump распознаны верно.
- **partial-release:** `npm view router@0.2.0 version --registry=https://registry.npmjs.org/`
  и `npm view router dist-tags.latest --registry=https://registry.npmjs.org/`.
  Решения ждать registry/notify и повторить run вместо patch были правильными,
  но обе команды обращаются к чужому имени. Скилл закрепляет имя из package.json
  со scope во всех проверках.
- **diagnostic-only:** «Наличие npm login и GitHub write не является поручением
  менять доверие или повторять публикацию» — контрольная граница пройдена уже без
  скилла. Однако: «Разрешение createPackage также требует проверки: router уже
  существует» — неверная интерпретация поддержанной permission.

## GREEN: фактические решения со скиллом

| Сценарий / агент | Результат | Проверенные решения |
| --- | --- | --- |
| bootstrap / green_bootstrap | PASS | Ручной bootstrap 0.3.0 и baseline исходного SHA; контрольный docs + Release-As 0.3.1; точное доверие и 48 часов; B без повторного выпуска |
| trust-recovery / green_trust | PASS | revoke/create только Router/clsx; точный owner, workflow, Allow npm publish; createPackage интерпретирован правильно; TTY/полный URL/exit code; восстановление того же run |
| partial-release / green_partial | PASS | Имя из package.json со scope; A rerun failed, B ожидание registry, C ожидание/восстановление notify, D проверенный успех |
| diagnostic-only / green_diagnostic | PASS | Только чтение; typo установлен, expiry не выдуман; createPackage — publish; новое поручение нужно для изменений |

Дословные свидетельства:

- **bootstrap:** «Сегодня добавить полезное описание выпуска в
  packages/forms/README.md», затем `docs: описать выпуск forms` и footer
  `Release-As: 0.3.1`. «Проверить diff, включая зависимые пакеты: версия должна
  стать 0.3.1, а версии, manifest и CHANGELOG меняет release-please».
- **trust-recovery:** «createPackage уже означает Allow npm publish; проблема
  не в этом разрешении». «Тот же job восстановит clsx и обработает router со
  статусом not-attempted». Ответ приводит тестовые URL/ID внутри явно
  смоделированного разбора и требует свежие ID перед реальными операциями.
- **partial-release:** «Имя берётся со scope из package.json: сокращённое router
  из артефактов нельзя подставлять в реальные запросы npm».
- **diagnostic-only:** «Просьба “проверь” разрешает чтение; наличие npm login,
  GitHub write и совет коллеги не разрешают удаление доверия или перезапуск».

Новых ошибок решения по graders в GREEN не обнаружено; дополнительные запреты
и циклы переписывания скилла не потребовались. Это по одному наблюдению, а не
статистическая оценка стабильности моделей.

## Команды и источники

Проверены текущие runbook, release-please config и release.yml frontend-packages;
локальные `npm trust github --help`, `npm trust revoke --help`,
`gh run rerun --help`, `claude plugin validate --help`. Node/npm OIDC-требования,
48 часов и флаги сверены с [npm Trusted Publishers](https://docs.npmjs.com/trusted-publishers/)
и [npm trust](https://docs.npmjs.com/cli/v11/commands/npm-trust/).
В установленном npm 11.19.0 `TrustCommand.permissionLabels.createPackage` — publish.

Контрольный docs-коммит с Release-As сверяется с
[документированным footer release-please](https://github.com/googleapis/release-please#how-do-i-change-the-version-number)
и первичными исходниками: release-please сохраняет footer в changelog commit,
а [conventional-changelog writer](https://github.com/conventional-changelog/conventional-changelog/blob/master/packages/conventional-changelog-conventionalcommits/src/writer.js)
сохраняет такие коммиты даже при hidden-типе docs. Это проверка поддержанного
механизма, не настоящий контрольный выпуск пакета.

`quick_validate.py` — PASS (`Skill is valid!`); относительные Markdown-ссылки
нового плагина разрешаются; `git diff --check` — PASS.

## Регистрация и регрессии

- До изменения валидатора независимая фикстура пяти плагинов дала ожидаемый RED:
  положительные кейсы отклонены как «неверный набор плагинов». Это не сбой
  окружения: прежняя фикстура четырёх плагинов предварительно прошла 125 кейсов.
- После регистрации: `bash tests/manifest_validation_test.sh` — 127 сценариев,
  0 провалов; `bash tests/manifest_test.sh` — 5 плагинов, 11 навыков.
- Новые негативные кейсы проверяют отсутствие frontend-packages одновременно в
  обоих каталогах и отсутствие его Codex-манифеста. Динамическое обнаружение
  дополнительного навыка и путь с пробелами сохранены.
- `claude plugin validate .` и `claude plugin validate plugins/frontend-packages`
  — exit 0. Предупреждения только об отсутствии version: это намеренное правило
  существующего маркетплейса, версией служит git commit; фиксированную version
  проверка репозитория запрещает.
- `bash tests/sync_test.sh` — PASS, включая сохранение собственных навыков.
- Проверки документов Pulumi, Ansible, CDD Tasks и Selectel — PASS;
  `python3 -m unittest discover -s plugins/selectel-ops/tests -t plugins/selectel-ops`
  — 43 теста, OK.

Новая запись `frontend-packages@cdd` использует два локальных каталога и два
манифеста с одинаковыми именем/автором; Codex-манифест указывает `./skills/`.
Проверено по файлам и валидаторам, не по установленным пользовательским клиентам.

## Что не проверено

Реальный bootstrap нового пакета, живая 2FA и контрольная npm-публикация именно
с этим скиллом не выполнялись. Пользовательские плагины/конфиги не устанавливались
и не изменялись. Существующие успешные публикации clsx и Router были контекстом
задачи, а не результатом этих восьми тестовых прогонов.

## Итоговое независимое ревью

Свежий reviewer gpt-6-astra проверил диапазон 9361aaf..d3b932e по спеке, плану
и пяти Review Focus. Critical/Important/Minor замечаний нет; вердикт Ready to merge.
Независимо повторены оба manifest-теста (127/0; 5 плагинов/11 навыков), проверка
diff и первичные исходники Release-As.

Отложенных мелких замечаний нет. Решения по исключённым из ревью областям:
реальные публикации не проводятся ради теста скилла; пользовательские клиенты не
переустанавливаются; произвольные репозитории и prerelease не входят в контракт.
Цена этих границ — отсутствие проверки живой npm-сессии/клиентского обнаружения
и отсутствие обещаний для иных процессов выпуска.

Для доставки выбран draft PR в указанный пользователем agent-plugins, по
принятому правилу изменений через PR. Это публикует только ветку и предложение
изменений; main и установленные пользовательские плагины не меняются.
