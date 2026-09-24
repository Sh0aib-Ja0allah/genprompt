# Worked examples (illustrative only, never copy the specifics)

> **Read this banner before borrowing anything.** These blocks are adapted from real archived
> prompts for a booking app (a React Native client in a monorepo, plus a Laravel backend). Names,
> documents and domain details have been changed. They show what a *strong* instance of each §4
> block looks like in practice.
>
> **Never copy their specifics into a prompt for another repo.** That includes file names, test
> counts, SHAs, routes, `apps/mobile`, `billing_address`, the `docs/0x_*` names and the "work on
> main, commit and push every slice" posture. Copy the *shape*. Take every specific from the repo
> you are actually targeting. The generic templates are in `guide/03-blocks.md`.
>
> Section numbers match `guide/03-blocks.md`.

### 4.1 Header (above the block, generator/user-facing)

```
| Date | 2026-07-27 |
| Archetype | D — slice execution (§5.D), with E-style rulings folded in |
| Target repo | c:\...\<repo>  ·  branch main  ·  scope apps/mobile |
| Follows | 2026-07-26-approve-...-r1-column-boundary-amendment.md |
```
`Follows` / `Amends` / `Depends on` / `Re-issues` is what makes the library a chain rather than a
pile. Never omit it when one applies.

### 4.2 Grounding notes (above the block, never sent to the worker)

The verified facts each instruction rests on, with `file:line`, SHAs, counts. This is the
generator's own anti-hallucination mechanism — if a claim has no line here, it does not belong in
the prompt.

```
**Grounded by:** read-only pass over <what>. Findings that reshaped the prompt:
- Home calls FIVE query hooks, not three (index.tsx:32-36) — the assessment undercounted.
- `summary.data === null` is a legitimate success (schemas.ts:296-297), never an error signal.
- The docs contradict each other: §2.6 says a response header, rule #44 says an endpoint. Backend has neither.
```

### 4.3 What the user asked for + Interpretations locked in (overridable)

```
## What the user asked for
1. <literal restatement>

## Interpretations locked in (stated to you, overridable)
**MFA: flag off, do not delete.** "For now" implies reversible. Deleting would discard the
authentication-bypass fix, turn re-enabling into a migration exercise, and orphan two test files.
```
The highest-leverage failure in this workflow is the generator silently turning "disable X" into
"delete X". This block makes reinterpretation visible before the prompt is pasted.

### 4.4 Situation — worker report ingested with hard numbers

```
## Situation
Items 1–3 landed (`61fab2a`, `2c2b119`, `7f043c9`). **253 tests / 2,377 assertions** (from 236/2,203),
pint clean, seed clean, 178 routes. Each committed green. Tree clean except the untracked probe file.
```
A numeric baseline is what lets the next prompt *require movement*. Without it a silently narrowed
suite reads as success.

### 4.5 Repo anchor + contract precedence (first lines inside the block)

```
Repo: ~/code/<repo>  (branch `main`; monorepo — apps/mobile IN scope, apps/admin +
packages/ + services/ OUT; do not touch them)

Read `CLAUDE.md` at the repo root FIRST — it is the binding conventions contract. Where this
prompt and `CLAUDE.md` disagree, follow `CLAUDE.md` and tell me.
IGNORE `~/code/CLAUDE.md` (found by the ancestor scan) — a different project, it does not govern
this repo.
```

### 4.6 Source of truth with authority annotations

```
1. `@docs/SPEC.md`                   <- binding, outranks the tech spec
2. `@docs/02_backend_techspec.md`
3. `docs/04_delivery_register.md` Part 3  <- the LIVE register; Parts 1-2 are a frozen snapshot
4. the repo's own `CLAUDE.md`        <- USEFUL BUT STALE: its debt list still shows C-01..C-07 open
                                        while the audit marks them fixed. Believe the code.
Where a doc and the code disagree, the code wins and the doc gets fixed.
```

### 4.7 Current-state skepticism with a falsifying example

```
CURRENT-STATE SKEPTICISM
- Do NOT assume any doc is still true. Both doc sets have known drift and contradict each other.
- Do NOT assume prior work is correct because it builds, lints, or has a passing test.
  `__tests__/screens/Payment.test.tsx` passes for a screen not registered in `NavigationRoutes.tsx`.
  Treat green tests as a claim to verify, not evidence.
- The register's ✅ marks are not trustworthy: twelve "delivered" items were re-checked and twelve
  failed, always by dropping the tail of the item's own definition. Hold each to its ORIGINAL
  definition, not to the tick.
```

### 4.8 MODE FOR THIS SESSION (autonomy contract)

```
MODE FOR THIS SESSION
- You have STANDING APPROVAL for everything in Parts A–F. Do not wait for me between parts.
- Work directly on `main`. No branches, no PRs.
- COMMIT AND PUSH AFTER EVERY SLICE, not at the end. Not optional: a silent file truncation earlier
  in this project was recoverable only because the file happened to be committed.
- Report at each boundary, then CONTINUE without waiting.
- Stop and ask ONLY for something in "WHAT YOU CANNOT DO", or something that contradicts this prompt.
```
Use this **or** the §4.19 approval gate. The gate is right for attended planning; this is right for
unattended execution. Never ship a prompt with neither.

### 4.9 The defect — mechanism, chain, consequence

```
THE DEFECT: Screens/Home/index.tsx calls FIVE query hooks (index.tsx:32-36) and branches on
`isLoading` exactly ONCE (:84). `isError` appears ZERO times. Every other section is gated on
truthiness of `.data`, so a failure is indistinguishable from "you have nothing" — on an
appointments error `upcoming.data` is undefined → `next` is undefined (:42) → :92-100 renders
"No upcoming appointments", telling a customer with a booking tomorrow that they have none.
```
This replaces bare scope bullets. A bullet admits a dozen implementations, most missing the point.

### 4.10 Decisions already made — do not re-litigate

```
DECISIONS ALREADY MADE — implement exactly these, do not re-litigate:
- BEHAVIOUR: hard block, full-screen overlay, single CTA, NO dismiss (SPEC.md §15:1271).
- PRE-AUTH: the gate sits ABOVE the auth decision — it must block logged-out users too (§3.4:211).
- DATA SOURCE: a dedicated `version` domain. Do NOT use the documented `x-min-app-version` header:
  the refresh call at client.ts:48 uses bare `axios`, so a response interceptor would miss it.
  Note the header as the documented alternative in a comment.
```
Include the **negative** decisions and why. An unattended worker meeting an open question either
stalls or guesses.

### 4.11 ⚠ TRAPS — per-item landmines

```
TRAPS — each of these will break a naive implementation:
• The demo `create` NEVER returns 409 and ignores idempotencyKey (Appointments.ts:47-65) — the
  conflict path is UNREACHABLE without a spy.
• TEXT COLLISIONS: the Stepper renders 'Provider' while the summary row also does — `getByText('Provider')`
  throws "found multiple elements".
• Demo delays are REAL (220ms / 600ms) and no test uses fake timers — `await findBy…`, never a bare
  `getBy` straight after an action.
```

### 4.12 Copy the right pattern — negative pattern selection

```
COPY THE RIGHT PATTERN — this is the trap: the MAJORITY of screens (MyAppointments:85-104) render the
error banner IN ADDITION to the empty state. Copying that leaves "No upcoming appointments" on screen
beside the error — the exact lie you are fixing. Copy instead the EXCLUSIVE chain at
MessagesInbox:41-71 (isLoading → isError → empty → data). Use MyAppointments only for prop spelling.
```
"Follow existing patterns" causes the bug when the majority pattern is the defective one.

### 4.13 WHAT YOU CANNOT DO — the stop-list

```
WHAT YOU CANNOT DO — do not attempt, do not fake, do not stub as if live
These need something only I can supply. Build to the boundary, label it, list exactly what you need:
- B7 mail transport — no SMTP credentials. Blocks every notification path.
- B6 hosting — MySQL 8, Redis, a queue supervisor. Do NOT flip notifications to `ShouldQueue`
  before a worker exists; that silently strands every notification rather than delaying it.
- G18 refunds — BLOCKED ON A CONTRADICTION I must resolve: `SPEC.md:230-233` makes the billing
  service the single source of truth while `RefundPolicy.php:20-21` defers to the payment
  provider's records. Do not write that migration until I rule.
Keep this list current and do not let it silently shrink.
```

### 4.14 Verification, DO/DON'T, DEFINITION OF DONE, REPORT

```
VERIFICATION — run before every commit. Never commit red.
    <literal command 1>
    <literal command 2>          <- this is what CI runs; branch coverage is the known-red gate
Report actual numbers, not "passes". Baseline is 30 suites / 159 tests — the count must go UP.
<environment facts: tools not on PATH, phar paths, memory flags>

DO: copy MessagesInbox's exclusive error chain; treat summary null as success; always pass
    retryLabel; reuse existing i18n keys; write order-independent tests.
DON'T: add ANY dependency; flip any domain live; hardcode a fabricated store ID; use `any` or raw
    hex; weaken or delete an existing test; touch packages/ or services/; create a branch or commit.

DEFINITION OF DONE: lint + typecheck + test green at each checkpoint (baseline 30/159 — must go UP).
Home surfaces errors per-section without lying about empty state, with a test proving the
empty-state copy is ABSENT on error. No dependency added, nothing flipped live, locale parity intact.

REPORT (do not commit): per checkpoint — what you built, the decisions you had to make that this
prompt did not cover, and the file list reconciled against `git status`. Plus gate numbers per
checkpoint, any existing test you touched and why, and confirmation that you stayed on main, added
no dependency, flipped nothing live, touched only apps/mobile, and left everything uncommitted.
```

### 4.15 Falsifiability standard

```
- Reproduce with a failing test FIRST, then fix, then keep the test.
- Prove the fix is load-bearing: stash it and confirm exactly the right cases go red. A fix whose
  absence does not fail a test is not proven.
- Adding a check where none existed → a positive control suffices. REPLACING one check with another
  → compare the admitted sets in both directions and test the delta, because a widening passes every
  existing test.
- Assert the legitimate case still succeeds before concluding a rule works. Without that,
  "everything returns 422" reads as a fix and ships as a regression.
```

### 4.16 Corrections to my previous prompt (generator conceding error)

```
1. YOUR DEVIATION IS RIGHT — my instruction was under-specified.
I told you to copy the gate `billing_address` uses without checking whether the two fields share an
audience. They do not. Keep `tax_id` in the array, and record the reasoning in the code, because
the next reader will see it diverge from `billing_address` and assume it is a mistake.

2. SEVERITY CORRECTION ACCEPTED. You are right and I was loose. That is a validation bypass, not
RCE, and I should have said so. Use your severity, not mine, in the report.
```
Two failures this prevents: a worker that deviated correctly re-applying the bad instruction next
turn, and — worse — a worker learning that deviations are unwelcome, which is exactly the behaviour
that lets a bad generator instruction ship.

### 4.17 Quote the worker, and quote the source, verbatim

Quote the worker's exact sentence before ruling on it — a paraphrase silently widens or narrows the
claim. Quote the governing spec line with `path:line` and then do the arithmetic:
*"RULE #40 VERBATIM (rules.md:585): 'Tests required for: Login, OTP verify, Booking wizard, Queue
tracker, Auth restoration.' FIVE suites. Three exist. Exactly TWO are missing. Build those two."*

### 4.18 The doc is wrong — follow the code

```
⚠️ THE RULES DOC IS WRONG ABOUT THE HARNESS — follow the CODE:
- Rule 38 says render via `renderScreen()` from `__tests__/mocks/screenTestUtils.tsx`. THAT FILE
  DOES NOT EXIST. The real helper is `renderWithProviders` from `@Core/Mocks/testUtils` (:38).
- Rule 39 says mock with MSW. Exactly ONE test does. All 9 screen tests use `jest.spyOn` — follow
  the code. Copy MessagesInbox.test.tsx:47 exactly.
```

### 4.19 Approval gate (attended mode only)

```
Do not start coding until I approve the plan, unless I explicitly say "continue immediately".
```

