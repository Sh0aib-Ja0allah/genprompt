# Utility: `/genprompt:profile [repo]`

Derive or refresh a repo's profile card without emitting a worker prompt.

1. **Resolve the target** (PROTOCOL Step 1) and narrow it to a code root.
2. **Check the cache** at `~/.genprompt/generated-prompts/by-repo/<key>.profile.md`. For each `stamp:` entry,
   compare it with `git log -1 --format=%h -- <file>` and check `git status --porcelain <file>`.
   Report whether the card is fresh (every stamp matches and none is dirty), stale (say which
   stamp moved), expired (past the 90-day ceiling, even with matching stamps) or missing, with its
   age in days (`today − derived`), as §2.9 defines. There is no shorter TTL.
3. **Derive** every field of §2.9, using `guide/01-target-profile.md` and `stacks/stack-matrix.md`.
   That includes the ancestor scan and the **gates** (shown, never cached).
4. **Print the card and the gates.** For a stale card, show a diff against the old one.
5. **Write the card** to `by-repo/<key>.profile.md`, unless the request has `--dry-run`. This is
   inside the write boundary. Never write anything into the repo.
6. **List the unknowns** a later prompt will have to ask about (§1, "facts that cannot be derived").
