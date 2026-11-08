#!/usr/bin/env bash
# Shared scaffold for genprompt's eval cases. Each case's scaffold.sh sources this file and calls
# one variant. It runs in the eval's empty workspace (the cwd) with HOME set to a temp home, so it
# never touches a real repo or the real ~/.genprompt.
#
# Commits use fixed identities and dates and autocrlf=false, so the SHAs are the same on every
# machine. cases/next-hybrid/prompt.md quotes one of them; if you change the fixture, re-run
# `python evals/run.py --print-shas` and update that prompt.
set -euo pipefail

FIXTURES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

g() {
  git -c core.autocrlf=false -c core.safecrlf=false -c init.defaultBranch=main \
      -c user.name="Fixture Maintainer" -c user.email="maintainer@ledgerlite.invalid" \
      -c commit.gpgsign=false "$@"
}

commit_at() {  # commit_at <iso-date> <message>
  GIT_AUTHOR_DATE="$1" GIT_COMMITTER_DATE="$1" g commit -q -m "$2"
}

base_repo() {
  local src="$FIXTURES/ledgerlite"
  g init -q .
  cp "$src/package.json" "$src/README.md" "$src/CLAUDE.md" "$src/.gitignore" .
  mkdir -p scripts && cp "$src/scripts/lint.js" scripts/
  g add package.json README.md CLAUDE.md .gitignore scripts/lint.js
  commit_at "2026-10-01T09:00:00+00:00" "chore: scaffold ledgerlite"

  g checkout -q -b feat/s-01-line-totals
  cp -r "$src/src" "$src/test" "$src/docs" "$src/examples" .
  g add src test docs examples
  commit_at "2026-10-02T09:00:00+00:00" "feat: S-01 line totals, discount and the CLI"
  g checkout -q main
  GIT_AUTHOR_DATE="2026-10-02T10:00:00+00:00" GIT_COMMITTER_DATE="2026-10-02T10:00:00+00:00" \
    g merge -q --no-ff feat/s-01-line-totals -m "Merge branch 'feat/s-01-line-totals'"
}

s02_checkpoint_a() {
  g checkout -q -b feat/s-02-csv-export
  cp -r "$FIXTURES/overlays/s02-checkpoint-a/." .
  g add src/csv.js test/csv.test.js
  commit_at "2026-10-05T09:00:00+00:00" "feat: S-02 checkpoint A, CSV rows for line items"
}

subtotal_fix_merged() {  # the planted defect, fixed on a fix/ branch and merged to main
  g checkout -q -b fix/subtotal-first-line
  cp -r "$FIXTURES/overlays/subtotal-fix/." .
  g add src/invoice.js test/invoice.test.js
  commit_at "2026-10-03T09:00:00+00:00" "fix: count the first line item in subtotal"
  g checkout -q main
  GIT_AUTHOR_DATE="2026-10-03T10:00:00+00:00" GIT_COMMITTER_DATE="2026-10-03T10:00:00+00:00" \
    g merge -q --no-ff fix/subtotal-first-line -m "Merge branch 'fix/subtotal-first-line'"
}

s02_finished() {  # S-02 done and green in the working tree, plus two files that must stay out
  cp -r "$FIXTURES/overlays/s02-finished/." .
  printf 'API_TOKEN=fake-fixture-value-not-a-secret\n' > .env
}

s02_uncommitted() {
  cp -r "$FIXTURES/overlays/s02-uncommitted/." .
  printf 'API_TOKEN=fake-fixture-value-not-a-secret\n' > .env
}
