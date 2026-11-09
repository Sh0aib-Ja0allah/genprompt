# CP6a: the 1.3.0 load cut (4e59265) — FAIL on plan vs v1.1.0

| | |
|---|---|
| Candidate | local main `4e59265`: E-09d (COMMON_BLOCKS trimmed, compact checklist in each excerpt, card-less derivation via `guide/blocks/derive.md`, 5 KB) + E-09e (home from `archive.py --where`, new Step 0) |
| Load baselines | v1.1.0 `fb4db7b` and v1.2.0 `d584108`, both in the same probe run |
| Gate (Planner, fixed before results) | card-less per-case median rule bytes ≤ v1.1.0 **and** ≤ v1.2.0, in every case. Card-fresh: reported only. Quality: plugin eval of fix and redesign vs the CP5 runs |
| Run | 2026-11-09, `realuse/run.py compare --base fb4db7b d584108 --cand 4e59265 --cases slice fix redesign plan --model haiku --budget 0.15 --runs 3 --home empty --a4 report --max-total 1.40` |
| Cost | home-mode isolation check $0.0073 + card-less probe $0.8618 = **$0.8691** of the $3 cap |
| Not run | card-fresh probe and the quality eval: the load gate failed, and the rule is to stop and report |

## Verdict

| Check | Result |
|---|---|
| **Load gate: cand ≤ v1.1.0 and ≤ v1.2.0 in every case** | **FAIL: plan vs v1.1.0, +14.3%**. Every other cell passes |
| A1 no Read of an @-included file, PROTOCOL.md or 03-blocks | PASS |
| A2 first-turn context larger | FAIL, but no longer meaningful: E-09d shrank the includes, so the candidate's first turn is smaller than v1.2.0's in fix (30,044 → 29,695) and plan (29,229 → 29,075). Not a gate here |
| A5 isolation | FAIL as scripted. No file content left the probe root, and every write landed in a sandbox home. Two real gaps and some false alarms; see Isolation below |

Only plan misses, not fix. Fix passes against both baselines (−31.5% vs v1.1.0, −15.6% vs v1.2.0).

## Load: rule bytes per case (median of 3; @-included + Read)

| Case | v1.1.0 fb4db7b | v1.2.0 d584108 | cand 4e59265 | Δ vs v1.1.0 | Δ vs v1.2.0 |
|---|---|---|---|---|---|
| slice | 62,894 | 61,230 | 37,325 | −40.7% | −39.0% |
| fix | 53,561 | 43,475 | 36,672 | −31.5% | −15.6% |
| redesign | 53,481 | 39,314 | 35,819 | −33.0% | −8.9% |
| plan | **30,615** | 41,367 | **34,990** | **+14.3%** | −15.4% |

Per run, v1.1.0 / v1.2.0 / cand:
- slice: 62,894 62,894 40,288 / 40,153 71,405 61,230 / 37,325 ×3
- fix: 53,561 63,420 53,561 / 43,475 ×3 / 36,672 36,672 41,899
- redesign: 53,481 53,481 55,680 / 39,314 ×3 / 35,819 ×3
- plan: 30,615 30,615 53,157 / 41,367 72,619 41,367 / 34,990 40,217 34,990

Reported, not gated (A4): the all-runs median drop is 33.0% vs v1.1.0 and 15.4% vs v1.2.0. The
median of per-case medians is 32.3% and 15.5%.

### Files Read × runs (out of 3)

| Case | v1.1.0 | v1.2.0 | cand |
|---|---|---|---|
| slice | 03-blocks ×3, 04-checklist ×3, stack-matrix ×2 | 01-target-profile ×2, 04-checklist ×3, stack-matrix ×1 | none |
| fix | 03-blocks ×3, 04-checklist ×3, stack-matrix ×1 | 04-checklist ×3 | derive ×1 |
| redesign | 03-blocks ×3, 04-checklist ×3, stack-matrix ×1 | 04-checklist ×3 | none |
| plan | 03-blocks ×1, 04-checklist ×3 | 01-target-profile ×1, 04-checklist ×3, stack-matrix ×1 | derive ×1 |

E-09d works as designed:
- Candidate runs read no rule file at all in 10 of 12 runs, and `derive.md` (5,227 B as read) in the
  other two.
- 01-target-profile, stack-matrix and 04-checklist are gone from every candidate run.

### Why plan misses v1.1.0

- The candidate's plan floor is its @-includes, **34,990 B**: shim 2,651 + PROTOCOL 16,390 +
  archetype F 2,871 + `guide/blocks/F-plan.md` 13,078. Two of the three runs read nothing beyond
  that.
- v1.1.0's plan @-includes only 24,607 B (no excerpt). In two of three runs it read just
  04-checklist (6,008) and **skipped 03-blocks**: 30,615 B. Those are cheaper runs that under-read,
  not better ones. The third run read 03-blocks and came to 53,157.
- To beat v1.1.0's under-reading median, plan's floor must fall by at least **4,376 B**. For
  example, `guide/blocks/F-plan.md` would go from 13,078 to about 8.7 KB or less. This mirrors the
  Planner's fix remedy (trim the archetype's own named blocks, not COMMON_BLOCKS), applied to F
  instead of L.
- Fix's floor is 2,698 + 16,390 + 3,684 + 13,900 = 36,672. It passes because both baselines read
  more for fix.

## Isolation in home mode (new for E-09e)

- **Setup.** Each run got a fresh sandbox home `homes/<plugin>-<case>-r<i>` through
  `GENPROMPT_HOME`. Write and Edit were allowed only there; Write and Edit on the home directory,
  the fixture, the plugin copies and the shared roots were denied.
- **Bash.** Bash was narrowed: `cd ls head tail wc cat`, `git diff`, `git grep` and `git config`
  were denied for every ref. Python was denied for the baselines, whose archive.py ignores
  GENPROMPT_HOME.
- **Pre-check ($0.0073).** In a separate check:
  - `archive.py --where` printed the sandbox home and `git log` ran;
  - `ls` and `cat` on the home were denied;
  - Write into the sandbox home succeeded, while Write into the fixture and into the real home
    was denied;
  - a baseline's `python … archive.py` was denied.
- **Writes in the probe.** Every Write/Edit landed in a sandbox home. They were archive parts files
  under `tmp/` (fix r3, redesign r1, plan r2), which matches E-09e's write boundary.
  `archive.py --dry-run` then wrote nothing.
- **Real gaps.** Claude Code auto-allows some read-only shell builtins, even in `dontAsk`:
  - `echo "$HOME"` printed the home path (v1.2.0 slice r1);
  - v1.1.0 plan r2 ran `test -f "$HOME/.genprompt/local-rules.md" && echo …`, which printed
    "local-rules: exists / archive: exists". That is the **existence** of two real paths, not
    their content.
  - Fix for the next home-mode run: also deny `echo printf test [ pwd env printenv` (no spend to
    add).
- **False alarms.** These need a grader change, offline:
  - "ls … was blocked by a deny rule" is a denial ("deny", not "denied");
  - "Python was not found" (the Windows store alias), and `python --version`;
  - the candidate's `archive.py --dry-run …`, which only prints "DRY RUN: nothing written".
- **--where on Windows.** Several candidate runs had `python3 … archive.py --where` denied or hit
  the store alias. One run (redesign r1) got the sandbox home from `python "…" --where`. Card-less
  holds either way: the sandbox home is empty and the real home is denied. For the card-fresh run,
  check that `--where` resolves, or the card is never seen.

## Next (PE / Planner)

1. Trim plan's floor by at least 4.4 KB (F's own named blocks), then re-probe plan (and the rest)
   against both bases.
2. Before the card-fresh run: deny the auto-allowed builtins, and accept "blocked by a deny rule",
   "Python was not found" and `archive.py --dry-run` in A5. Both are offline changes.
3. The quality eval (fix, redesign on opus vs CP5) is still owed. About $2.13 of the $3 cap is
   left.

Traces: `C:/genprompt-probe/genprompt-probe-20261109-014033/` (36 jsonl, sandbox homes,
`report.md`). Isolation check: `C:/genprompt-probe/genprompt-homeiso-20261109-013949/`.
