## 3. Core principles

1. **Anchor the repo.** Give the absolute path, the branch, and the sub-scope in a monorepo. Never
   leave it ambiguous.
2. **State one sharp task** in one or two sentences, before any detail.
3. **Name the conventions contract and give it precedence.** *"Read `CLAUDE.md` first. It is the
   conventions contract. Where this prompt and it disagree, follow it and tell me."*
4. **Give an ordered source of truth**, with authority markers and exclusions (§2.6).
5. **Back skepticism with a falsifying artifact.** "Don't trust green tests" is a posture, and a
   posture is ignorable. A finding is not: *"`<a test file>` passes for `<a thing that does not
   work>`, because `<the reason>`."* The artifact must come from **this** repo.
6. **Ground every instruction.** Cite `file:line` for anything load-bearing, and mark the rest
   `[UNVERIFIED]`. Never invent a path, a script name, a line number or a count.
7. **Make scope items mechanisms, not bullets.** Each one names the mechanism at `file:line`, the
   causal chain, and the consequence a user sees.
8. **Constrain hard and negatively.** Name what is out of scope, by path, and what must not be
   faked.
9. **Put literal gates in every prompt, with a stated baseline and its expected delta.**
   - The delta is **up** for new behaviour and tests, **unchanged** for commits, refactors,
     cleanup and docs, and **down** only with a named reason.
   - "All green" alone is satisfiable by deleting tests.
   - A mid-session delta prompt restates the gates. It never says "same as last time".
10. **State the git posture, positively and negatively:** branch, commit cadence, staging method,
    and whether to push. Take it from the contract. Where the prompt deviates, say so explicitly.
11. **Specify the report, with negative confirmations** and a `git status` reconciliation.
12. **End with a terminal imperative:** `Start with Part A now.` or `Continue.` Never trail off.
13. **Make autonomy a contract, not a default.** A code-writing prompt carries **either** an
    approval gate **or** a `MODE FOR THIS SESSION` block with a named stop-list, never neither and
    never both. A read-only or commit-only prompt (B, F, H, M, N, P, W) states `N/A: read-only` or
    `N/A: commit-only`, and bounds its writes by enumeration instead.
14. **Put durable findings in the repo's docs** and method in its methodology doc. Neither goes in
    chat as a code dump. **The exception is a chat-only report**, allowed for reviews, closeouts and
    any prompt run against an occupied tree (§4.27). There a new repo doc would collide with
    another session. The generator's archive then keeps the record.
15. **Verify by reading, never by running.** The generator checks the worker's claims against
    commits, diffs and files, and labels each number `verified by artifact` or `reported`. Running
    the gates is the worker's job.
16. **Keep the prompt within its budget.** Every archetype has a length budget (§4.21). Restated
    context the worker already holds is noise, and noise hides the instruction that matters.

---
