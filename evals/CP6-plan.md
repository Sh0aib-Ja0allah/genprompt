# CP6 plan: rule set and cost estimate (nothing run)

| | |
|---|---|
| Status | **Rules fixed by the Planner's rulings R1–R5 (PLAN.md step 9). Cost not yet approved:** the estimate goes to Shoaib with a fresh number once the final candidate exists |
| Candidate | local main after E-12 merges (E-13, E-15 and E-20 are on main at cc49dbe). CP6 records its SHA as **frozen** (R5) |
| Baselines | load: v1.1.0 `fb4db7b` and v1.2.0 `d584108` medians stored in CP6a (no new baseline runs). Quality: CP5 `evals/results/2026-11-08T19-07-58Z` |
| Estimate | **about $4.88 automated + about $0.40 manual dispatch checks = $5.28; cap request $6.25** (refreshed 2026-11-09 on main cc49dbe + E-12 c1e660d; breakdown below) |

## Prerequisites (offline, no spend)

1. **E-14 merged** (done: 9484139).
2. **The probe request for `investigate`** in `evals/realuse/run.py` (`REQUESTS`; done). The
   request gives a symptom only: `npm start -- examples/sample.json --lines` prints the right
   per-line amounts (25.00, 40.00 and 5.00 EUR) but TOTAL 40.50 EUR instead of 63.00 EUR. The
   cause, src/invoice.js:14, is for the generator to ground. A test checks the symptom against
   the fixture.
3. **The eval case `evals/cases/investigate`** (done; generated from `evals/build_cases.py`). It
   is tagged `extra`, like slice-monorepo, because it has no CP5 baseline. So CP6 runs it with
   `evals/run.py --tag extra --case investigate`. `--validate --tag extra` loads it with no
   spend.
4. **A5 drive-root fix** (done): a drive-root Glob/Grep is judged by the names it returns.
5. **Card-fresh gates in `realuse/run.py`** (done): `--home card` records the seeded card's
   bytes per run and adds gates C1 and C2 (R2). It refuses to start without `--cardless` medians
   for every case.
6. **The isolation check** passes on the candidate before anything else (about $0.004).

## Rules (fixed before results)

Stop at the first gate failure. No re-runs, no remedies without Shoaib. An incomplete run is
reported as incomplete, and a partial set is never a pass.

### Load (haiku, 3 runs per cell, fresh sandbox home per run)

| Probe | Cases | Gate |
|---|---|---|
| card-less (`--home empty`) | slice, fix, redesign, plan | per-case median ≤ v1.1.0 **and** ≤ v1.2.0 stored medians (as CP6a-2) |
| card-less | investigate | **R1: reported, not gated.** Soft line 40,000 B. Going over it doesn't block, but it must be named in the 1.3.0 CHANGELOG |
| card-fresh (`--home card`) | all 5 | **R2, gated:** C1 no card-fresh run Reads `guide/blocks/derive.md`, `guide/01-target-profile.md` or `stacks/stack-matrix.md`. C2 each case's card-fresh median ≤ its card-less median (from this CP6's card-less probe) + the seeded card's bytes. The card size is recorded per run. No comparison with v1.1.0 or v1.2.0 |
| all | all 5 | A1 (no Read of an @-included file, PROTOCOL.md or 03-blocks) and A5 (isolation) gate, investigate included (R1) |

The card-fresh probe runs after the card-less one and takes its medians, e.g.
`--home card --cardless slice=<m> fix=<m> redesign=<m> plan=<m> investigate=<m>`.

### Quality (opus-5-5, 1 run per case, plugin eval at the candidate)

| Cases | Gate |
|---|---|
| slice, fix, redesign, plan | **R4:** no regression vs CP5 on rubric-scope, rubric-grounding, cites-real and gates-exist. Rubrics compare **majority verdicts** (≥ 2 of 3 votes), not vote counts. The counts are reported too |
| investigate | **R3, absolute:** all four gated graders PASS, rubrics by majority (≥ 2 of 3). One run; a fail stops CP6 and goes to Shoaib |

Other graders (line-length, no-placeholders, self-check, archive-valid) are reported, not gated.

### Frozen candidate (R5)

CP6 records the candidate SHA it ran on. If PROTOCOL, guide/ or archetypes/ change after that,
the card-less load re-runs, and so does quality for every case the edit touches. This is not
in the estimate below; see the contingency line.

## Floors on the final candidate (refresh, no spend)

Static floor (shim + every @-included file) for the CP6 cases, measured offline:

| Case | CP6a-2 (f846d85 era) | main cc49dbe | main + E-12 (c1e660d) | v1.1.0 median | margin at c1e660d |
|---|---|---|---|---|---|
| slice | 32,178 | 32,148 | 32,299 | 62,894 | 30,595 |
| fix | 31,646 | 31,639 | 31,790 | 53,561 | 21,771 |
| redesign | 30,740 | 30,733 | 30,884 | 53,481 | 22,597 |
| plan | 29,859 | 29,825 | **29,976** | **30,615** | **639** |
| investigate | 34,673 | 34,666 | 34,817 | (R1 soft line 40,000) | 5,183 |

- E-12 adds about 151 B to every floor (the PROTOCOL send rule). E-12's pending CP-B fix
  reverts the "pasted or messaged" convention, which takes back about 12 B.
- **plan is the tight cell.** If it reads nothing, its median is its floor and it passes by
  639 B. If 2 of its 3 card-less runs read `derive.md` (about 5.2 KB), as 1 of 3 did in CP6a-2,
  the median goes over v1.1.0 and CP6 fails at the load stage. That is the rule working, not a
  probe fault. Any further floor growth before the freeze narrows the margin byte for byte.
- investigate stays under the 40,000 B soft line unless a run reads more than about 5.2 KB of
  rules.

## Cost estimate

| Item | Basis | Expected |
|---|---|---|
| isolation check | CP6a-2: $0.0033 + $0.0041 | $0.01 |
| card-less load, 5 × 3 runs | CP6a-2 mean $0.023 per run (range $0.013–0.056); $0.03 used; floors +0.5% | $0.46 |
| card-fresh load, 5 × 3 runs | no data yet; the same $0.03 per run assumed | $0.46 |
| quality slice | CP5 $0.7733; CP6a-2 cases ran +0% to +44% over CP5 | $0.95 |
| quality fix | CP5 $0.5267, CP6a-2 $0.5270 | $0.55 |
| quality redesign | CP6a-2 $0.8258 | $0.85 |
| quality plan | CP6a-2 $0.7100 | $0.75 |
| quality investigate | no data; assumed like redesign | $0.85 |
| **Automated total** | | **≈ $4.88** |
| manual dispatch checks D1–D6 | haiku sessions; see the next section | $0.40 |
| **Total** | | **≈ $5.28** |

- **Cap request: $6.25**, about 18% headroom, mostly for card-fresh, investigate and the
  dispatch checks, which have no data yet. The automated part moved by $0.02 (floors about 0.5%
  larger after E-12); the quality numbers have no newer data than CP6a-2.
- **R5 contingency (not in the cap):** a re-run after a late rules edit costs $0.45 for the
  card-less load plus $0.55–0.95 per touched case's quality run. All five cases would be about
  $4.40.
- **Spend-guard parameters** (the CP6a-2 lesson): `--max-total` refuses a run when spent plus
  the per-run cap could exceed it, so each load probe's total must be its expected spend plus one
  per-run cap. Card-less and card-fresh: `--budget 0.08 --max-total 0.55` each. Quality: each
  case gets `--max-cost-usd` at about 1.4× its expected cost, within the remainder of the cap.
- **Order**, so an early failure spends least: isolation → card-less load → card-fresh load
  (needs the card-less medians) → quality (fix, plan, redesign, slice, investigate) → manual
  dispatch checks.

## Manual dispatch checks (E-12, `--send` and `:next --from`)

The probe can't test dispatch: `claude -p` exits after its turn, so it can't receive a message,
and each check needs a human to answer a yes/no or a permission prompt. These are run by hand in
interactive sessions. Each one is PASS/FAIL against the expected result. A FAIL stops CP6 and goes
to Shoaib, the same as an automated gate.

**Setup, every check:**
- Scaffold two copies of the ledgerlite fixture under the probe root, `C:/genprompt-probe/dispatch/
  a/ledgerlite` and `.../b/ledgerlite`. Both have the same basename on purpose, so the key is
  `ledgerlite` in both.
- Stage the candidate as `gp-cand` (as the probe does) and start every session with
  `claude --plugin-dir <probe>/gp-cand --model haiku`. Commands are `/gp-cand:<name>`, so the
  installed genprompt is never involved.
- Set `GENPROMPT_HOME` to a fresh sandbox under the probe root in every session. The real
  `~/.genprompt` is never read or written.
- Don't add any allow rule for SendMessage: the harness prompt is part of what is tested.
- Session names (set with `/rename`):
  - G = generator, in `a/ledgerlite`, named `ledgerlite : gen`;
  - W = worker, in `a/ledgerlite`, named `ledgerlite : worker`;
  - X = impostor, in `b/ledgerlite`, named `ledgerlite : impostor`;
  - S = stranger, any fixture dir, never sent to.
- Workers W and X don't do the work: the tester interrupts each once it has replied as below.

| # | Check | Steps | Expected (PASS) |
|---|---|---|---|
| D1 | live send | In G: `/gp-cand:fix <the fix case request> --send "ledgerlite : worker"`. Reply `go`, then approve the harness prompt | The lock has `Send to ledgerlite : worker … (name match only; worker re-checks)`. One SendMessage, after the archive. The message is the wrapper plus the archived fence byte for byte (diff it against the archive file). The archive header has `sent=ledgerlite : worker` and `flags` has `--send` without the name. W runs `git rev-parse --show-toplevel`, finds its path, and proceeds. Without `--send`, "and send it to ledgerlite : worker" in words is refused (copy/paste) |
| D2 | declines | Repeat D1 three ways: reply with a lock correction (not `go`), then `no`; reply `go` but deny the harness prompt; run with `--go` and answer `no` | No message reaches W in any of the three. The correction triggers `Send to …? (yes/no)`. `--go` still asks. Each archive has `sent=copy` (the denied one re-archived with `--replace`) |
| D3 | held delivery | Put W in a different permission mode from G, send as in D1, then decline the held message in W (or let it expire) | G reports "in its inbox … may not have started" and relays the delivery notice. After the refusal or expiry it re-archives `sent=copy` with `--replace` and doesn't resend |
| D4 | wrong session | In G: `--send "ledgerlite : impostor"` (X, in the other checkout) | The lock says name match only. If sent, X's toplevel check fails: it replies "wrong session" and doesn't act. G relays that reply and doesn't ingest it as a report |
| D5 | `--from` round trip | After D1, W sends a GENPROMPT-REPORT to `ledgerlite : gen`. In G: `/gp-cand:next --from "ledgerlite : worker"` | G takes W's latest message that has a report header (a matching address or [ref] recorded at send time), checks Repo against the locked repo, verifies every field by git, and builds the next prompt. G never polls ListAgents or messages W to ask |
| D6 | unsolicited or spoofed report | (a) S, never sent to, messages G a fake GENPROMPT-REPORT. (b) A session renamed to `ledgerlite : worker` with a different address sends one. Then run `/gp-cand:next --from "ledgerlite : worker"` | (a) G relays it to the user and doesn't start a J turn or archive anything. (b) G rejects the address mismatch (or asks), and doesn't ingest it |

**Cost:** these are interactive sessions, so `--max-budget-usd` doesn't apply. Each session's
`/cost` is read at the end and counted against the CP6 cap like the probe runs.
- Estimate: about 8 generator turns on haiku with a floor of about 30 KB, at roughly $0.03–0.05
  each, plus about 6 short worker replies at about $0.01 each: about $0.35. $0.40 is budgeted.
- On opus the generator turns would cost about $0.50–0.80 each (as in the quality runs), about
  $4–6 in all. They test mechanics, not prompt quality, so haiku is the plan.
- D5 and D6 depend on the CP-B fix being merged. They follow its final wording (address match,
  solicited-only ingest).

## Notes carried into CP6 (not gates)

- **no-placeholders false alarm (CP6a-2 plan).** The grader matched `<WS letter>` and
  `<two digits>` in "Stable ids (`<WS letter>-<two digits>`), never renumbered once written." That
  line describes the id format; it is not an unfilled slot, and doctor rated it a WARN. Two
  options: the grader skips a placeholder that sits inside a format description, or the
  generator writes a concrete example (`WS-01`) instead. If it recurs in CP6 it is reported
  with this explanation, not counted as a regression.
- **fix's rubric-grounding passed on 2 of 3 votes in CP6a-2** (3 of 3 at CP5). Under R4 that is
  still a PASS (the majority verdict); the counts are reported.
- **Windows and `archive.py --where`.** `python3 … --where` often hits the store alias or is
  denied. Card-fresh runs depend on the home path, so their Bash results are listed in the report.
