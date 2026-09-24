# 5.W: Documentation · `/genprompt:docs`

| | |
|---|---|
| **Use when** | Write or repair a README, API docs, a runbook, an admin/user guide, handover docs, or architecture docs that drifted from the code |
| **Not when** | Designing something not yet built → `:design`. A contract for an unfamiliar repo → `:onboard` |
| **Autonomy** | N/A: docs only. Writes are enumerated (the named doc files) |
| **Baseline delta** | Unchanged: no code changes. A doc-lint or link-check gate runs if the repo has one |
| **Length tier** | Focused (200) |
| **Deliverable** | The named docs, every factual claim checked against the code, and a drift list of what was wrong before |

## Generator: before emitting

- **Name the audience and the language.** For example, an Arabic admin guide for a client, or an
  API reference for integrators. Audience decides depth and vocabulary. If the contract says
  client wording is contractual, quote it verbatim and never paraphrase it.
- **List the facts the doc must carry and their sources in code:** commands from the manifests,
  routes from the route files, env keys from `.env.example`, screens from the panel resources.
- **Drift check:** name the claims you already found stale (`file:line` in the doc against
  `file:line` in the code).
- **Screenshots and images** are placeholders unless the worker can produce real ones. Mark them.

## Required blocks

- §4.5, §4.6, §4.18 (the doc is wrong: follow the code)
- §4.20 explicit tool allow-list (enumerated doc writes)
- §4.14 (doc gates only)

## Template

```text
Repo: <PROFILE.path> (branch <PROFILE.branch>)
[INSERT §4.5 contract precedence]
Task: <write | repair> <doc> for <audience>, in <language>. You may WRITE ONLY: <doc paths> (plus the
contract's mandated tools, if any). No code changes. <git posture: commit the docs per the contract | leave uncommitted>.

[INSERT §4.6 source of truth: the code outranks every doc]
[INSERT §4.18 THE DOC IS WRONG: <stale claims found: doc:line vs code:line>]

CONTENT (each fact verified in code, with its source path noted in your report, not in the doc):
1. <section>: <facts it must carry> (source: <paths>)
2. <section>: …
Style: <audience-appropriate; the contract's language/terminology rules; RTL/bidi rules if Arabic>.
<Contractual wording: quote verbatim from <doc>; never rewrite it.>

REPORT: the files written; a drift list (claim before → truth → source); anything you could not
verify ([UNVERIFIED]); placeholders left for me. Confirm that no code changed.
Start with section 1.
```
