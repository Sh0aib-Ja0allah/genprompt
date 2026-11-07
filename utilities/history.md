# Utility: `/genprompt:history [repo] [n]`

Emits no worker prompt. Read-only.

1. **Resolve the repo** with PROTOCOL Step 1 (argument ▸ continuation ▸ cwd ▸ ask) and compute its
   key (§10.1). With no repo and none resolvable, list every shard in `by-repo/` instead, with each
   one's latest row date and row count.
2. **Read** `~/.genprompt/generated-prompts/by-repo/<key>.tsv`. Skip every `#` line, including a legacy shard's
   final `# --- v3 ---` marker. Parse the 5 `|`-separated fields (tolerate missing spaces around
   `|` and a trailing empty task). Legacy rows may be over-long: show them anyway, and mark them
   `legacy`.
3. **Sort by date, then by file mtime** (legacy backfilled rows are not strictly ordered). Show the
   last `n` rows (default 10) as a table: date · archetype · slug · file (or status) · task
   (truncated to 80 characters).
4. **Show the chain for the latest prompt.** Read its line-1 header (or its §4.1 table) for
   `follows`/`Amends`, and walk back up to 5 links. Say where a link does not resolve.
5. **Show the profile card status:** present / stale (the date, or which stamp changed) / missing.
6. **Show this repo's measures**, read from the line-1 headers of its prompt files (the same three
   counts `/genprompt:doctor` prints for the whole archive, PROTOCOL Step 6 item 2 vocabulary):
   - `via`: argument / continuation / cwd / ask
   - `lock`: go / accepted / corrected, with the correction rate (corrected ÷ (accepted + corrected))
   - flag use: how many prompts carried `--go`, `--brief`, `--dry-run`, `--verbose`, `--unattended`

   Count only files whose header has `flags`, `via` or `lock`, and say how many older files predate
   the fields ("N older files predate the fields"). Never flag those files: they are valid.
7. **End with one line:** the likely next command, derived from the latest row (for example: the
   latest is a slice with no commit row after it, so `/genprompt:commit` or `/genprompt:next` with
   the report).
