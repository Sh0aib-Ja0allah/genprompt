# CP6a-2: E-09f floor cut (f846d85) — INCOMPLETE

| | |
|---|---|
| Candidate | `f846d85` (E-09f: every archetype's always-loaded floor cut by about 5.2 KB; plan's floor is 29,853 B) |
| Rule (fixed before results) | load: card-less per-case median ≤ v1.1.0 and ≤ v1.2.0, using CP6a's stored baseline medians. Quality: fix, redesign and plan on opus vs CP5 `2026-11-08T19-07-58Z`. Stop at the first failure; an incomplete run is reported as incomplete |
| Run | 2026-11-09: isolation check, then `realuse/run.py compare --cand f846d85 --cases slice fix redesign plan --model haiku --budget 0.15 --runs 3 --home empty --max-total 0.40` |
| Cost | isolation $0.0033 + $0.0041, load $0.2623 = **$0.2697** of $2.13 (about $1.86 left) |
| Status | **INCOMPLETE.** The spend guard stopped the load probe after 11 of 12 runs (plan r3 not run). Load is not decided for plan, so the quality eval was not run |

## Isolation check (drive root)

- **First attempt ($0.0033): passed, but proved nothing.** The isolation probe has no plugin, so
  nothing granted Glob. Under `dontAsk`, the drive-root Glob was refused for that reason, not by
  the new deny rules.
- **Fix.** The probe now grants Read/Glob/Grep the way every shim's `allowed-tools` does, so only
  the deny rules seal it.
- **Second attempt ($0.0041): PASS.**
  - The 5 home and shared-root calls were denied, and the work dir was readable.
  - The drive-root `**/*.md` Glob ran and returned only paths under the probe root (0 outside).
- **The real runs agree.** Two candidate runs (slice r1, plan r1) Globbed `CLAUDE*.md` from `C:/`.
  They got only fixtures under `C:/genprompt-probe` and the run's own `CLAUDE.md`. In CP6a the same
  kind of call listed 101 system file names.
- **A5 still flags these two calls.** It judges a call by its path (`C:/` is outside), not by the
  names it returns. That is a grader false alarm. Proposed offline fix: for a Glob/Grep whose path
  is the drive root, check the returned names against the probe root instead.

## Load (11 of 12 runs; haiku, card-less, fresh empty sandbox home per run)

| Case | @-included (floor) | per-run rule bytes | median | v1.1.0 median | v1.2.0 median | vs v1.1.0 | vs v1.2.0 |
|---|---|---|---|---|---|---|---|
| slice | 32,178 | 37,405 32,178 32,178 | 32,178 | 62,894 | 61,230 | −48.8% | −47.4% |
| fix | 31,530 | 31,530 37,763 31,530 | 31,530 | 53,561 | 43,475 | −41.1% | −27.5% |
| redesign | 30,705 | 30,705 30,705 35,932 | 30,705 | 53,481 | 39,314 | −42.6% | −21.9% |
| plan | 29,853 | 35,080 29,853 *(r3 not run)* | **undecided** | 30,615 | 41,367 | — | — |

- slice, fix and redesign pass against both baselines on complete 3-run medians.
- **plan is undecided.** Its floor (29,853) is now below v1.1.0's median (30,615).
  - r1 read `derive.md` (35,080); r2 read nothing (29,853).
  - The median of 3 is r3's value, clamped to [29,853, 35,080]: it passes if r3 ≤ 30,615.
  - The missing run therefore decides the plan gate.
- Rule files read across all 11 runs: `derive.md` ×4 (slice r1, fix r2, redesign r3, plan r1) and
  `stacks/ladders/node.md` ×1 (fix r2). No 01-target-profile, stack-matrix, 04-checklist or
  03-blocks. A1 holds: no Read of an @-included file, PROTOCOL.md or 03-blocks.
- Bash: no unsafe command ran. `archive.py --where` hit the store alias or was denied in most runs.
  The candidate's `archive.py --dry-run` ran in redesign r3 and wrote nothing.

## Why it stopped (my parameters)

- `--max-total` refuses to start a run when `spent + --budget` (the per-run cap, $0.15) could
  exceed the total. With a $0.40 total, it can only guarantee runs while spend is at most $0.25.
- The 12-run estimate was $0.28, so these parameters were bound to stop near the end. They did,
  at $0.2623 after 11 runs. The guard did its job; the cap pair was my mistake.
- With a $0.05 per-run cap, the same $0.40 total would have covered all 12. Per-run cost here was
  $0.013–$0.056.

## To finish (needs a GO)

1. Run plan r3 only: one haiku run, about $0.03, with the same flags and a $0.05 per-run cap. That
   decides the plan median.
2. If load passes: run fix, redesign and plan on opus with `--max-cost-usd` set to what's left
   (about $1.83 against the $1.61 estimate).

Traces: `C:/genprompt-probe/genprompt-probe-20261109-031359/` (11 jsonl; no `report.md`, since the
guard exits before writing it). Isolation: `C:/genprompt-probe/genprompt-isolation-20261109-031337/`.
