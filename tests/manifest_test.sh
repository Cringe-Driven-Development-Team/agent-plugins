#!/usr/bin/env bash
# Общие исходники навыков обслуживают каталоги Claude Code и Codex.
# Без фиксированной version обновления получают версию коммита.
set -uo pipefail

fail() { echo "  FAIL: $*" >&2; exit 1; }
[ "$#" -le 1 ] || fail 'использование: manifest_test.sh [repo_root]'
ROOT=$(cd -P "${1:-$(dirname "${BASH_SOURCE[0]}")/..}" && pwd -P) || fail 'недоступен корень маркетплейса'
CLAUDE=$ROOT/.claude-plugin/marketplace.json
CODEX=$ROOT/.agents/plugins/marketplace.json
EXPECTED='["ansible","cdd-tasks","pulumi","selectel-ops"]'

check_json() {
  [ -f "$1" ] || fail "${1#"$ROOT"/}: нет файла"
  jq -e -s 'length == 1 and (.[0] | type == "object")' "$1" >/dev/null 2>&1 \
    || fail "${1#"$ROOT"/}: ожидается один JSON-объект"
}

check() {
  jq -e "$2" "$1" >/dev/null 2>&1 || fail "${1#"$ROOT"/}: $3"
}

read_json() {
  jq -r "$2" "$1" || fail "${1#"$ROOT"/}: не удалось прочитать $2"
}

STRING='def text: type == "string" and length > 0;'
check_json "$CLAUDE"
check_json "$CODEX"
check "$CLAUDE" "$STRING .name == \"cdd\" and (.owner | type == \"object\")
  and (.owner.name | text) and (.metadata | type == \"object\")
  and (.metadata.description | text) and (.plugins | type == \"array\")" 'неверные поля каталога'
check "$CODEX" '.name == "cdd" and (.interface | type == "object")
  and .interface.displayName == "Cringe Driven Development"
  and (.plugins | type == "array")' 'неверные поля каталога'

for catalog in "$CLAUDE" "$CODEX"; do
  check "$catalog" "$STRING all(.plugins[]; type == \"object\"
    and (.name | text and test(\"^[a-z0-9]+(-[a-z0-9]+)*$\")) and (has(\"version\") | not))" \
    'неверная запись плагина или фиксированная version'
  duplicates=$(read_json "$catalog" '.plugins | group_by(.name) | map(select(length > 1) | .[0].name) | join(", ")') \
    || fail "${catalog#"$ROOT"/}: не удалось найти дубли"
  [ -z "$duplicates" ] || fail "${catalog#"$ROOT"/}: повторные имена: $duplicates"
  names=$(read_json "$catalog" '.plugins | map(.name) | sort | tojson') \
    || fail "${catalog#"$ROOT"/}: не удалось прочитать имена"
  [ "$names" = "$EXPECTED" ] || fail "${catalog#"$ROOT"/}: неверный набор плагинов: $names"
done
check "$CLAUDE" "$STRING all(.plugins[]; (.source | text) and (.description | text))" 'неверная форма записей'
check "$CODEX" 'all(.plugins[]; (.source | type == "object") and .source.source == "local"
  and (.source.path | type == "string") and (.policy | type == "object")
  and .policy.installation == "AVAILABLE" and .policy.authentication == "ON_INSTALL"
  and .category == "Productivity")' 'неверный локальный источник, политика или категория'

SKILLS=0
PLUGINS=0
for name in ansible cdd-tasks pulumi selectel-ops; do
  expected_path=./plugins/$name
  for catalog in "$CLAUDE" "$CODEX"; do
    if [ "$catalog" = "$CLAUDE" ]; then field='.source'; else field='.source.path'; fi
    source_path=$(read_json "$catalog" ".plugins[] | select(.name == \"$name\") | $field") \
      || fail "${catalog#"$ROOT"/}: не удалось прочитать источник $name"
    [ "$source_path" = "$expected_path" ] \
      || fail "${catalog#"$ROOT"/}: $name: источник должен быть $expected_path, получено $source_path"
  done
  plugin=$ROOT/plugins/$name
  [ -d "$plugin" ] || fail "plugins/$name: нет корня плагина"
  canonical=$(cd -P "$plugin" && pwd -P) || fail "plugins/$name: не удалось разрешить путь"
  case "$canonical" in "$ROOT"/*) ;; *) fail "plugins/$name: источник за пределами маркетплейса" ;; esac

  claude_manifest=$plugin/.claude-plugin/plugin.json
  codex_manifest=$plugin/.codex-plugin/plugin.json
  for manifest in "$claude_manifest" "$codex_manifest"; do
    check_json "$manifest"
    check "$manifest" "$STRING (.name | text) and (.description | text)
      and (.author | type == \"object\") and (.author.name | text) and (has(\"version\") | not)" \
      'неверные поля манифеста или фиксированная version'
    manifest_name=$(read_json "$manifest" '.name') || fail "${manifest#"$ROOT"/}: не удалось прочитать имя"
    [ "$manifest_name" = "$name" ] || fail "${manifest#"$ROOT"/}: имя не совпадает с $name"
  done
  claude_author=$(read_json "$claude_manifest" '.author.name') || fail "${claude_manifest#"$ROOT"/}: не удалось прочитать автора"
  codex_author=$(read_json "$codex_manifest" '.author.name') || fail "${codex_manifest#"$ROOT"/}: не удалось прочитать автора"
  [ "$claude_author" = "$codex_author" ] || fail "${codex_manifest#"$ROOT"/}: автор не совпадает с Claude Code"
  check "$codex_manifest" '.skills == "./skills/"' 'skills должен указывать на целое ./skills/'

  [ -d "$plugin/skills" ] || fail "plugins/$name/skills: нет каталога навыков"
  skill_files=$(find "$plugin/skills" -type f -name SKILL.md) || fail "plugins/$name/skills: не удалось прочитать дерево"
  [ -n "$skill_files" ] || fail "plugins/$name/skills: нет SKILL.md"
  while IFS= read -r skill_file; do
    [ -f "$skill_file" ] || fail "plugins/$name/skills: недоступен $skill_file"
    SKILLS=$((SKILLS + 1))
  done <<< "$skill_files"
  PLUGINS=$((PLUGINS + 1))
done
echo "манифесты в порядке: плагины=$PLUGINS, скиллы=$SKILLS"
