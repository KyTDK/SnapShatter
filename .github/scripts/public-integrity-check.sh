#!/usr/bin/env bash
set -euo pipefail

repository=${1:-.}
pattern=${PUBLIC_INTEGRITY_PATTERN:-}
metadata=${PUBLIC_INTEGRITY_METADATA:-}
base_sha=${PUBLIC_INTEGRITY_BASE_SHA:-}
head_sha=${PUBLIC_INTEGRITY_HEAD_SHA:-HEAD}

if [[ -z "$pattern" ]]; then
  echo 'public integrity policy is not configured' >&2
  exit 1
fi

cd "$repository"
git cat-file -e "${head_sha}^{commit}"

if printf '%s\n' "$metadata" | LC_ALL=C grep -Eiq -- "$pattern"; then
  echo 'public metadata did not pass integrity policy' >&2
  exit 1
fi

if [[ -n "$base_sha" ]]; then
  git cat-file -e "${base_sha}^{commit}"
  commit_range="${base_sha}..${head_sha}"
else
  commit_range="$head_sha"
fi

if git log --format='%B%n' "$commit_range" | LC_ALL=C grep -Eiq -- "$pattern"; then
  echo 'commit metadata did not pass integrity policy' >&2
  exit 1
fi

if git ls-tree -r --name-only "$head_sha" | LC_ALL=C grep -Eiq -- "$pattern"; then
  echo 'tracked path did not pass integrity policy' >&2
  exit 1
fi

if git grep -I -q -i -E -- "$pattern" "$head_sha" -- .; then
  echo 'tracked content did not pass integrity policy' >&2
  exit 1
fi
