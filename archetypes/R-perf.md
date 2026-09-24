# 5.R: Performance · `/genprompt:perf`

| | |
|---|---|
| **Use when** | Something is slow or heavy (page load, bundle size, query count/N+1, memory, API p95, app start, build time), or a target metric is set |
| **Not when** | There is no symptom and no target: do not optimise speculatively |
| **Autonomy** | Measure first (read-only + measurement), then optimise behind §4.19, or §4.8 if `--unattended` |
| **Baseline delta** | The **metric** must improve by a stated amount. Tests unchanged or up; behaviour unchanged |
| **Length tier** | Program (350) |
| **Deliverable** | A before/after measurement table per change (§4.24), the changes, and the rejected ideas with their numbers |

## Generator: before emitting

- **Pick the measurable metric and the tool from the stack:**
  - **Web:** build output size, Lighthouse/Web Vitals, network waterfall
  - **Laravel:** query count per request (debugbar/telescope/`DB::listen` in a test), response time
  - **Node API:** autocannon/k6 locally
  - **Flutter/RN:** frame timings, app size
  - **SQL:** `EXPLAIN`
- **State the environment.** Measure in production build mode where it matters, and never against
  production data or servers.
- **Name candidate hotspots from the code** (`file:line`) as hypotheses, not conclusions.

## Required blocks

- §4.5, §4.7, §4.24, §4.14
- §4.10 (behaviour must not change)
- §4.19 **or** §4.8

## Template

```text
Repo: <PROFILE.path> (branch <PROFILE.branch><, scope <root>>)
[INSERT §4.5 contract precedence]
Task: make <symptom/area> faster/lighter. Target: <metric> from ~<current, if known> to <target>.

[INSERT §4.24 MEASURE FIRST: metrics <…>, commands <…>, environment <build mode, machine, data size>]
Hypotheses, from reading (verify, don't assume): <file:line: suspected cause>, <…>.

STEP 1: measure the baseline. Profile, and find where the time/bytes/queries actually go.
        Rank the causes by measured share.
STEP 2: present the plan: the changes in order of expected gain / risk.
[INSERT §4.19 approval gate, or §4.8 MODE]
STEP 3: one change at a time; re-measure after each; keep it only if it wins; revert if not.
        Behaviour must not change: [INSERT §4.10: <what must stay identical>].
STEP 4: final table: metric | before | after | delta, per change, plus rejected changes with their numbers.

[INSERT §4.14: gates <literal>; tests unchanged or up; DON'T add caching layers/dependencies without asking]
Start with STEP 1 now.
```
