---
type: llm
weight: 3
---

Ответ хорош, если одновременно:
1. Основная задача и frontend PR находятся в `Cringe-Driven-Development-Team/frontend`; учебный frontend — копия main.
2. Инфровая часть — отдельная задача в `Cringe-Driven-Development-Team/infra`, привязанная к основной как sub-issue (именно sub-issue, а не ссылка в тексте или упоминание).
3. Заголовки задач начинаются с области: `Frontend. …` у основной и `DevOps. …` у инфровой.
4. В описании задач есть разделы «Цель», «Что сделать» и «Приёмка».
5. Оба PR закрывают свои задачи короткими строками `Closes #N`; frontend вливается последним после обязательного review ментора.
6. В смешанной фазе backend PR ещё направляется в go-park-mail-ru/2026_2_Cringe_Driven_Development со строкой `Closes Cringe-Driven-Development-Team/backend#56`.
Ответ плох, если рабочий frontend PR уходит в учебную копию, задачи заводятся в курсовых репозиториях, одна задача закрывается двумя PR, backend переносится раньше своей фазы или обходится review.
