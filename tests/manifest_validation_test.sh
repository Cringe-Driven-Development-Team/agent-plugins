#!/usr/bin/env bash
# Независимые фикстуры проверяют контракт валидатора, а не текущие тексты навыков.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
VALIDATOR=$ROOT/tests/manifest_test.sh
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
FIXTURE=$TMP/fixture
FAILS=0
CASES=0
case_root=
CLAUDE_CATALOG=.claude-plugin/marketplace.json
CODEX_CATALOG=.agents/plugins/marketplace.json
CLAUDE_MANIFEST=plugins/ansible/.claude-plugin/plugin.json
CODEX_MANIFEST=plugins/ansible/.codex-plugin/plugin.json

fail() { echo "  FAIL: $*"; FAILS=$((FAILS + 1)); }

make_fixture() {
  mkdir -p "$FIXTURE/.claude-plugin" "$FIXTURE/.agents/plugins"
  jq -n '{name:"cdd", owner:{name:"Team"}, metadata:{description:"Fixture"},
    plugins:["pulumi","ansible","selectel-ops","cdd-tasks"]} | .plugins |=
    map({name:., source:("./plugins/" + .), description:"Fixture"})' \
    > "$FIXTURE/$CLAUDE_CATALOG"
  jq '{name, interface:{displayName:"Cringe Driven Development"}, plugins:
    [.plugins[] | {name, source:{source:"local", path:.source},
      policy:{installation:"AVAILABLE", authentication:"ON_INSTALL"}, category:"Productivity"}]}' \
    "$FIXTURE/$CLAUDE_CATALOG" > "$FIXTURE/$CODEX_CATALOG"
  local name count i
  for name in pulumi ansible selectel-ops cdd-tasks; do
    mkdir -p "$FIXTURE/plugins/$name/.claude-plugin" "$FIXTURE/plugins/$name/.codex-plugin"
    jq -n --arg name "$name" '{name:$name, description:"Fixture", author:{name:"Team"}}' \
      > "$FIXTURE/plugins/$name/.claude-plugin/plugin.json"
    jq '. + {skills:"./skills/"}' "$FIXTURE/plugins/$name/.claude-plugin/plugin.json" \
      > "$FIXTURE/plugins/$name/.codex-plugin/plugin.json"
    case "$name" in pulumi) count=6 ;; ansible) count=2 ;; *) count=1 ;; esac
    i=1
    while [ "$i" -le "$count" ]; do
      mkdir -p "$FIXTURE/plugins/$name/skills/skill-$i"
      printf -- '---\nname: skill-%s\ndescription: Fixture\n---\nFixture\n' "$i" \
        > "$FIXTURE/plugins/$name/skills/skill-$i/SKILL.md"
      i=$((i + 1))
    done
  done
}

make_case() {
  CASES=$((CASES + 1))
  case_root=$TMP/case-$CASES-$1
  cp -R "$FIXTURE" "$case_root"
}

expect_ok() {
  local out status=0
  out=$(bash "$VALIDATOR" "$1" 2>&1) || status=$?
  [ "$status" -eq 0 ] || fail "$1: ожидался успех, код $status: $out"
  [[ "$out" == *"$2"* ]] || fail "$1: нет итога '$2': $out"
}

expect_fail() {
  local out status=0
  out=$(bash "$VALIDATOR" "$1" 2>&1) || status=$?
  [ "$status" -ne 0 ] || fail "$1: ожидался ненулевой код: $out"
  [[ "$out" == *"$2"* ]] || fail "$1: в диагностике нет '$2': $out"
}

mutate() {
  jq "$2" "$case_root/$1" > "$case_root/mutation.json"
  mv "$case_root/mutation.json" "$case_root/$1"
}

test_valid_inventory() {
  make_case valid
  expect_ok "$case_root" 'плагины=4, скиллы=10'
}

test_missing_catalog() {
  make_case missing-catalog
  rm "$case_root/$CODEX_CATALOG"
  expect_fail "$case_root" "$CODEX_CATALOG"
}

test_invalid_json() {
  local broken_file
  for broken_file in "$CLAUDE_CATALOG" "$CODEX_CATALOG" "$CLAUDE_MANIFEST" "$CODEX_MANIFEST"; do
    make_case invalid-json
    printf '{' > "$case_root/$broken_file"
    expect_fail "$case_root" "$broken_file"
  done
}

test_required_fields() {
  local broken_file field fields mutation
  for broken_file in "$CLAUDE_CATALOG" "$CODEX_CATALOG" "$CLAUDE_MANIFEST" "$CODEX_MANIFEST"; do
    case "$broken_file" in
      "$CLAUDE_CATALOG") fields='.name .owner .owner.name .metadata .metadata.description .plugins .plugins[0].name .plugins[0].source .plugins[0].description' ;;
      "$CODEX_CATALOG") fields='.name .interface .interface.displayName .plugins .plugins[0].name .plugins[0].source .plugins[0].source.source .plugins[0].source.path .plugins[0].policy .plugins[0].policy.installation .plugins[0].policy.authentication .plugins[0].category' ;;
      "$CLAUDE_MANIFEST") fields='.name .description .author .author.name' ;;
      "$CODEX_MANIFEST") fields='.name .description .author .author.name .skills' ;;
    esac
    for field in $fields; do
      for mutation in "del($field)" "$field = null" "$field = 42"; do
        make_case required-field
        mutate "$broken_file" "$mutation"
        expect_fail "$case_root" "$broken_file"
      done
    done
  done
}

test_wrong_values() {
  local broken_file mutation
  for broken_file in "$CLAUDE_CATALOG" "$CODEX_CATALOG"; do
    make_case wrong-marketplace-name
    mutate "$broken_file" '.name = "other"'
    expect_fail "$case_root" "$broken_file"
  done
  for mutation in '.interface.displayName = "Other"' '.plugins[0].source.source = "git"' \
    '.plugins[0].policy.installation = "REQUIRED"' '.plugins[0].policy.authentication = "NONE"' \
    '.plugins[0].category = "Other"'; do
    make_case wrong-value
    mutate "$CODEX_CATALOG" "$mutation"
    expect_fail "$case_root" "$CODEX_CATALOG"
  done
  make_case wrong-skills
  mutate "$CODEX_MANIFEST" '.skills = "./skills/skill-1/"'
  expect_fail "$case_root" "$CODEX_MANIFEST"
}

test_duplicate_name() {
  make_case duplicate-name
  mutate "$CODEX_CATALOG" '.plugins += [.plugins[0]]'
  expect_fail "$case_root" pulumi
}

test_different_plugin_set() {
  make_case different-set
  mutate "$CODEX_CATALOG" '.plugins[3].name = "other"'
  expect_fail "$case_root" "$CODEX_CATALOG"
}

test_mismatched_identity() {
  local mutation
  for mutation in '.name = "other"' '.author.name = "Other"'; do
    make_case identity
    mutate "$CODEX_MANIFEST" "$mutation"
    expect_fail "$case_root" "$CODEX_MANIFEST"
  done
}

test_missing_plugin_files() {
  local missing
  for missing in plugins/cdd-tasks plugins/cdd-tasks/.codex-plugin/plugin.json \
    plugins/cdd-tasks/skills plugins/cdd-tasks/skills/skill-1/SKILL.md; do
    make_case missing-files
    rm -rf "$case_root/$missing"
    expect_fail "$case_root" cdd-tasks
  done
}

test_unsafe_source() {
  local value broken_file
  for broken_file in "$CLAUDE_CATALOG" "$CODEX_CATALOG"; do
    for value in /outside ./../outside ./plugins/pulumi/skills/skill-1; do
      make_case unsafe-source
      if [ "$broken_file" = "$CODEX_CATALOG" ]; then
        mutate "$broken_file" ".plugins[0].source.path = \"$value\""
      else
        mutate "$broken_file" ".plugins[0].source = \"$value\""
      fi
      expect_fail "$case_root" pulumi
    done
  done
  make_case external-symlink
  cp -R "$case_root/plugins/pulumi" "$TMP/external-pulumi"
  rm -rf "$case_root/plugins/pulumi"
  ln -s "$TMP/external-pulumi" "$case_root/plugins/pulumi"
  expect_fail "$case_root" pulumi
}

test_fixed_version() {
  local broken_file
  for broken_file in "$CLAUDE_CATALOG" "$CODEX_CATALOG" "$CLAUDE_MANIFEST" "$CODEX_MANIFEST"; do
    make_case fixed-version
    case "$broken_file" in
      *marketplace.json) mutate "$broken_file" '.plugins[0].version = "1.0.0"' ;;
      *) mutate "$broken_file" '.version = "1.0.0"' ;;
    esac
    expect_fail "$case_root" "$broken_file"
  done
}

test_dynamic_inventory() {
  make_case dynamic-inventory
  mkdir -p "$case_root/plugins/pulumi/skills/new-skill"
  printf 'Fixture\n' > "$case_root/plugins/pulumi/skills/new-skill/SKILL.md"
  expect_ok "$case_root" 'плагины=4, скиллы=11'
}

test_root_with_spaces() {
  make_case 'root with spaces'
  expect_ok "$case_root" 'плагины=4, скиллы=10'
}

make_fixture
for t in $(declare -F | awk '$3 ~ /^test_/ {print $3}'); do
  echo "$t"
  "$t"
done
echo "сценариев: $CASES, провалов: $FAILS"
[ "$FAILS" -eq 0 ]
