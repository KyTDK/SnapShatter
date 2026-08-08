#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
checker="$script_dir/public-integrity-check.sh"
fixture="$(mktemp -d)"
trap 'rm -rf -- "$fixture"' EXIT

git -C "$fixture" init -q
git -C "$fixture" config user.name "Integrity Test"
git -C "$fixture" config user.email "integrity@example.invalid"
printf '%s\n' clean >"$fixture/clean.txt"
git -C "$fixture" add clean.txt
git -C "$fixture" commit -q -m "chore: initial fixture"
base="$(git -C "$fixture" rev-parse HEAD)"
pattern='forbidden-marker|blocked-path'

expect_failure() {
  label=$1
  shift
  if "$@" >/dev/null 2>&1; then
    printf 'FAIL: %s unexpectedly passed\n' "$label" >&2
    exit 1
  fi
}

expect_success() {
  label=$1
  shift
  if ! "$@" >/dev/null 2>&1; then
    printf 'FAIL: %s unexpectedly failed\n' "$label" >&2
    exit 1
  fi
}

expect_failure missing-policy env -u PUBLIC_INTEGRITY_PATTERN \
  PUBLIC_INTEGRITY_HEAD_SHA="$base" bash "$checker" "$fixture"
expect_success clean env PUBLIC_INTEGRITY_PATTERN="$pattern" \
  PUBLIC_INTEGRITY_HEAD_SHA="$base" bash "$checker" "$fixture"
expect_failure metadata env PUBLIC_INTEGRITY_PATTERN="$pattern" \
  PUBLIC_INTEGRITY_METADATA='forbidden-marker' \
  PUBLIC_INTEGRITY_HEAD_SHA="$base" bash "$checker" "$fixture"

git -C "$fixture" commit -q --allow-empty -m 'forbidden-marker'
head="$(git -C "$fixture" rev-parse HEAD)"
expect_failure commit env PUBLIC_INTEGRITY_PATTERN="$pattern" \
  PUBLIC_INTEGRITY_BASE_SHA="$base" PUBLIC_INTEGRITY_HEAD_SHA="$head" \
  bash "$checker" "$fixture"
git -C "$fixture" reset -q --hard "$base"

printf '%s\n' clean >"$fixture/blocked-path.txt"
git -C "$fixture" add blocked-path.txt
git -C "$fixture" commit -q -m 'chore: path fixture'
head="$(git -C "$fixture" rev-parse HEAD)"
expect_failure path env PUBLIC_INTEGRITY_PATTERN="$pattern" \
  PUBLIC_INTEGRITY_BASE_SHA="$base" PUBLIC_INTEGRITY_HEAD_SHA="$head" \
  bash "$checker" "$fixture"
git -C "$fixture" reset -q --hard "$base"

printf '%s\n' forbidden-marker >"$fixture/content.txt"
git -C "$fixture" add content.txt
git -C "$fixture" commit -q -m 'chore: content fixture'
head="$(git -C "$fixture" rev-parse HEAD)"
expect_failure content env PUBLIC_INTEGRITY_PATTERN="$pattern" \
  PUBLIC_INTEGRITY_BASE_SHA="$base" PUBLIC_INTEGRITY_HEAD_SHA="$head" \
  bash "$checker" "$fixture"

printf '%s\n' 'public integrity tests passed'
