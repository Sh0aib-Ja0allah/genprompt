## 10. Prompt library (archive spec, v3)

```text
~/.genprompt/                    <- the genprompt home: per user, outside every repo and the plugin
  local-rules.md                 <- optional personal rules (written by :learn)
  generated-prompts/             <- the archive
    by-repo/
      <key>.tsv                  <- append-only shard, one row per prompt or status event
      <key>.profile.md           <- cached profile card (§2.9)
      unsorted.tsv               <- deliverables with no repo
    <key>/
      <YYYY-MM-DD>-<cmd>[+<cmd>]-<slug>.md
    INDEX.md, flat files         <- ONLY in an archive migrated from genprompt v1/v2: frozen.
                                    Read; never append, rename or move.
```

The first archived prompt creates the folders. Nothing in the archive is ever written into a repo.

### 10.1 Keys and filenames

- **`<key>`** is the repo directory's basename, lowercased, with `_` and spaces turned into `-`
  (`Billing-Website` → `billing-website`, `Mobile_App_Backend` → `mobile-app-backend`). The folder and
  the shard use the same key. On a collision with a different path, suffix the key `-2` and note it
  in the profile.
- **Filename:** `<YYYY-MM-DD>-<cmd>[+<cmd>]-<slug>.md`.
  - `<cmd>` is the **command word** of each archetype in the label, dominant first. The words are
    `redesign audit kickoff slice approve plan greenfield commit roadmap next resume fix onboard
    design test review security perf upgrade release hotfix cleanup docs`.
    Examples: `next+fix`, `audit+fix`.
  - `<slug>` is kebab-case, lowercase, 60 characters at most. Name the work (`seo-structured-data`),
    not the finding's headline sentence.

### 10.2 The archive file

**Line 1, exactly** (a machine-readable header; `follows` is `-` when there is none):

```html
<!-- genprompt v3: key=<key> | repo=<DirName> | path=<abs path> | date=<YYYY-MM-DD> | archetype=<letters, e.g. J+L> | follows=<prior filename or -> -->
```

**Then, in order:**
1. the §4.1 header table
2. grounding notes and interpretations (§4.2, §4.3)
3. **the complete fenced prompt**
4. the §6 self-check table
5. an optional `## The transferable rule from this turn`

**A file without the full prompt is a defect.** "See the transcript" breaks the chain the library
exists to keep.

### 10.3 The shard

A **new** shard starts with these three lines, and every row in it is v3:

```text
# genprompt shard: <key>  (path: <abs path>)
# Fields: date | archetype | slug | file | task (<=200 chars)
# schema: v3
```

A **legacy** shard (one created before 2026-09-23) has the third line
`# schema: legacy rows first; v3 rows go below the marker line at the end of this file`. It
contains exactly one marker line, `# --- v3 ---`.
- Append new rows **below the last line** of the file. Do not insert above the marker, and do not
  quote the marker text anywhere else, because an edit anchored on it must match exactly once.
- Doctor holds a row to v3 rules if it is below the marker, if it is in a pure v3 shard, or if it is
  dated 2026-09-24 or later. Other rows count as legacy INFO.

**Prompt row** (5 fields, separated by ` | `):

```text
2026-09-23 | J+L | seo-structured-data | 2026-09-23-next+fix-seo-structured-data.md | Fix JSON-LD graph omissions; add Course schema test
```

- **archetype:** letters joined by `+`, dominant first (`J+D+L`). Never `→`, `×` or command words.
- **file:** a bare filename when it lives in `<key>/`, `<otherkey>/<file>` when it lives
  elsewhere, and `-` for a status row.
- **task:** 200 characters at most. No `|`, no `·`, no em-dash. The detail lives in the file, not
  in the row.

**Status row** (a turn that emitted no prompt):

```text
2026-09-23 | none | home-read-closeout | - | status: verified, no prompt emitted; all 12 items confirmed on main at abc1234
```

A status row names the SHA it verified or closed at. That lets a later review map commits back to
the prompts that produced them.

**Order.** Rows are appended in chronological order. `/genprompt:history` sorts by date and then
by file mtime, because legacy backfilled rows are not strictly ordered.

### 10.4 Lookups (use the Read and Grep tools; the generator has no cat or grep in Bash)

- **The latest prompt for a repo:** the last **data** row of `by-repo/<key>.tsv`. Skip `#` lines:
  a legacy shard ends with its marker. Or run `/genprompt:history <repo>`.
- **Which prompt produced a commit:** match by date and subject against the shard, or read the
  brief's own HEAD anchor. A commit with no matching row is labelled "no brief".
- **Everything for a repo:** Read the whole shard.
- **Legacy flat history:** Grep the root `*.md` for the repo name. It is a prose scan, so it
  confuses "targets" with "mentions".

### 10.5 Rules

- **Archive every emitted prompt**, unless the request has `--dry-run`. A no-prompt turn gets a
  status row.
- **Never append to `INDEX.md`.** Never rename or move a prompt file: `Follows` and `Amends`
  references point at exact filenames.
- **Shard rows may be normalised** (format, order, duplicates), but only with a snapshot copy in
  `~/.genprompt/history/` first. Prompt files are never edited after they are archived.
- **The integrity check is `tools/doctor.py`** (`/genprompt:doctor`). v3 rules are enforced from
  2026-09-23; earlier drift is reported as legacy INFO.

---
