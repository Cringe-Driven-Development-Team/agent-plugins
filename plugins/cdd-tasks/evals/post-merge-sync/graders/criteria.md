---
type: llm
weight: 3
---

Ответ хорош, если одновременно:

1. Разделяет frontend и backend: frontend merged/open/Ready for build без Release
   нормально; Release/Ready for release не означает выкатку. Backend закрывается
   при merge. Зелёный PR Check не доказывает post-merge CI, sync или production.
2. Выбирает ci.yml push/main по проверяемому полному SHA, проверяет code jobs и
   course-sync / sync; сверяет текущие main team/course. При продвижении main
   переходит к новому SHA перед заявлением об актуальности копии.
3. Даёт deploy-free путь: gh run rerun CI_RUN_ID --job SYNC_JOB_ID именно для sync,
   либо gh workflow run sync-to-course.yml --ref main -f ci_run_id=CI_RUN_ID
   в командном репозитории. ID run должен относиться к ci.yml push/main с
   успешными обязательными code jobs; общий красный CI из-за sync допустим.
4. Сначала проверяет, не восстановила ли копию более новая синхронизация; не
   повторяет старый SHA поверх нового. После повтора сверяет job и текущие main.
5. Оставляет backend merged PR и closed issue без переоткрытия из-за ошибки sync.
   Frontend не закрывает вручную ради исправления sync или ожидания CD.
6. Объясняет ❌ при ошибке, ✅ при успешном повторе того же failed run, тишину при
   обычном успехе и повторе после успеха. Новый ручной run не даёт recovery о
   другом run; Re-run старого запуска сохраняет прежний pin автоматики.
7. Делает вывод об успехе по jobs и SHA, а не по отсутствию Telegram-сообщения.
8. Для frontend Done требует успешного Health check и сохранённого production
   success. Проверяет Release, SHA Deployment, статусы Deployment и связанный run;
   один зелёный Health check при ошибке записи success не достаточен.
9. Для подтверждённого успешного deployment даёт
   `gh workflow run reconcile-issues.yml -R Cringe-Driven-Development-Team/frontend --ref main -f deployment_id=4242`.
   До команды проверяет источник/тип/успех и актуальность deployment, после — run,
   issue.state/stateReason и поле Status. Не подменяет ID новым или старым наугад,
   не повторяет deploy и не закрывает задачи вручную. При неподтверждённом success
   останавливает recovery и диагностирует исходный run.
10. Сохраняет Rollback from production и закрытость после rollback; позднее событие
    не отменяет актуальный результат. Ручной reopen защищён от повторов старого
    merge, новый связанный merge начинает новый цикл. Ручное completed до CD
    сохраняет Done, merge/публикация не возвращают задачу в Ready.

Ответ плох, если предлагает Re-run all jobs как sync-only восстановление,
перезапускает deploy ради копирования, работает в учебном repo, обходит provenance,
применяет force push или обещает recovery после любого успешного запуска.
Отсутствие точной процедуры frontend recovery — пробел руководства, а не успех.
Команды с ясно обозначенными переменными/плейсхолдерами допустимы.
