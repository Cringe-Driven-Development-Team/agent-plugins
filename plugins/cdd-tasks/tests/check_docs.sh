#!/usr/bin/env bash
# Только структура документов и evals; поведение проверяется отдельными прогонами.
set -u
cd "$(dirname "$0")/../skills/cdd-tasks" || exit 2
fail=0
need() { grep -qF -- "$2" "$1" || { echo "нет в $1: $2"; fail=1; }; }

[ -f SKILL.md ] || { echo "нет SKILL.md"; fail=1; }
need SKILL.md "name: cdd-tasks"
need SKILL.md "description:"
for h in "## Карта: где задача, где код" "## Завести задачу" \
         "## Треки и граф модулей" "## После merge" \
         "## Работа затрагивает несколько репозиториев" "## Что писать в описании PR" \
         "## Задача без PR" "## Чего ты не делаешь" "## Что сообщить человеку"; do
  need SKILL.md "$h"
done
for s in "CONTRIBUTING.md" "Cringe-Driven-Development-Team/frontend" \
         "Cringe-Driven-Development-Team/backend" \
         "frontend-park-mail-ru/2026_2_Cringe_Driven_Development" \
         "go-park-mail-ru/2026_2_Cringe_Driven_Development" \
         "Closes #N" "Part of" "sub-issue" \
         "web-N" "API-N" "«Цель», «Что сделать» и «Приёмка»" "--admin"; do
  need SKILL.md "$s"
done

for h in "## 1. Шаблон описания задачи" "## 2. Задача и sub-issue" "## 3. Доска" \
         "### Привязать трек к графу модулей" "### Разрешение и проверка merge" \
         "## 4. Pull request" "## 5. Задача без PR" \
         "## 6. После merge: CI и учебная копия" \
         "## 7. Frontend: Release, production и восстановление задач"; do
  need REFERENCE.md "$h"
done
for s in "## Цель" "## Что сделать" "## Приёмка" "sub_issue_id" "gh project item-add" \
         "gh project item-edit" "closingIssuesReferences" \
         "gh auth refresh -s project" "reconcile-issues.yml" \
         "deployment_id=" "--match-head-commit"; do
  need REFERENCE.md "$s"
done

for scenario in multi-repo-task next-sprint post-merge-sync merge-authorization module-track; do
  for file in prompt.md graders/criteria.md graders/skill.md; do
    path="../../evals/$scenario/$file"
    [ -f "$path" ] || { echo "нет $path"; fail=1; }
  done
done

# Упакованный скрипт должен запускаться через интерпретатор без доступа к API.
python3 scripts/set_sprint.py --help >/dev/null || fail=1

# id полей и итераций в документах не зашиваем: они меняются.
if grep -nE 'PVT(I|SSF|IF)?_[A-Za-z0-9_-]{10,}' SKILL.md REFERENCE.md; then
  echo "в документах зашит id проекта или поля"; fail=1
fi

[ "$fail" -eq 0 ] && echo "документы cdd-tasks в порядке"
exit "$fail"
