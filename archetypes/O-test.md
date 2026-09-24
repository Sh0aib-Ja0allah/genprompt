# 5.O: Test engineering · `/genprompt:test`

| | |
|---|---|
| **Use when** | Write missing tests, raise coverage in a named area, fix vacuous or flaky tests, or stand up an E2E/integration harness |
| **Not when** | A test exposes a product bug that must be fixed now → record it, then `:fix` |
| **Autonomy** | Code-writing (tests and test infrastructure only): §4.8 MODE or §4.19 gate |
| **Baseline delta** | Up: test count and assertions (and coverage, if it is measured). A deleted or weakened test needs a reason |
| **Length tier** | Focused (200) |
| **Deliverable** | New or repaired tests, green, each proven to fail without the behaviour it guards |

## Generator: before emitting

- **Read the existing test setup:** runner, helpers, factories/fixtures, mocks, CI config. Name
  the helper to reuse and the pattern to copy (§4.12). Test code copies the majority pattern even
  when it is wrong.
- **For each target, name the behaviour to pin,** not the function to call. Use the spec line, the
  route, or the user-visible outcome.
- **Vacuous tests:** list each suspected one with why it cannot fail (it asserts on a mock, has no
  assertion, or matches a string that always renders).
- **Flaky tests:** name the nondeterminism source (time, order, network, randomness, shared DB
  state).
- **Production code is out of scope.** A product defect a test exposes is RECORDED, not fixed. The
  only exception is a test seam the contract allows.

## Required blocks

- §4.5, §4.7, §4.12, §4.14, §4.15
- §4.20 RECORD, DO NOT ACT
- §4.24, if coverage or timing is measured
- §4.8 **or** §4.19

## Template

```text
Repo: <PROFILE.path> (branch <PROFILE.branch><, scope <root>>)
[INSERT §4.5 contract precedence]
Task: <write | repair | harden> tests for <area>. Production code is OUT of scope.

[INSERT §4.8 MODE or §4.19 gate]
Test setup, as I read it: runner <…>, helpers <path:line>, factories/fixtures <…>, CI runs <…>.
[INSERT §4.12 COPY THE RIGHT PATTERN: the helper and test to copy, and the majority pattern to avoid]

TARGETS (each is a behaviour, not a function):
1. <behaviour> (spec: <doc:line> | route <…>): assert <outcome>; also assert <negative/edge>.
2. <vacuous test path:line>: it cannot fail because <reason>. Rewrite it so it fails when <X> breaks.
3. <flaky test path:line>: nondeterminism from <source>. Remove the source; do not retry-loop it.

[INSERT §4.15 falsifiability: every new test must FAIL when the behaviour is removed. Show it]
[INSERT §4.20 RECORD, DO NOT ACT: a product bug found by a test goes to <doc>, with a failing test
 marked skipped + the reason, or kept as a documented known-failure per the contract]
[INSERT §4.24 measurement, if coverage/timing matters]

[INSERT §4.14: gates <literal>; baseline <tests/assertions> → expected at least <n+k>; DON'T touch
 production code, weaken assertions, or add a test dependency without asking]
Start with target 1 now.
```
