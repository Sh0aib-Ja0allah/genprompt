# D1–D6 hand run: `--send` and `:next --from` (checklist for Shoaib at the keyboard)

| | |
|---|---|
| What it tests | The dispatch mechanics of guide/06-library.md §10.8: the yes per send, the name and project check, the prompt-only payload, held delivery, the worker's toplevel check, and solicited-only report ingest. It does **not** test prompt quality. |
| Model | haiku in every session |
| Cost estimate | **about $0.45–0.65**; suggested cap **$0.80**. See the end. Interactive sessions have no `--max-budget-usd`, so read `/cost` in each session at the end. |
| Spend | **Needs Shoaib's OK before step 0.** |
| Time | about 40–60 minutes |

Fill in the PASS/FAIL column as you go. **Stop at the first FAIL** and send the table to the PE.

## Step 0: set up (offline, no spend)

1. In a terminal in the genprompt checkout:
   `python evals/realuse/run.py dispatch-setup --cand <candidate SHA>`
   - It stages the candidate as `gp-cand`, scaffolds two ledgerlite checkouts (`a/ledgerlite`, `b/ledgerlite`)
     and four empty sandbox homes.
   - It prints one start command per session and saves them to `<work dir>/sessions.txt`.
2. Open **four** terminal windows: G, W, X and S. In each, paste that session's command from
   sessions.txt. Each command does three things:
   - `cd` into the right checkout;
   - set `GENPROMPT_HOME` to that session's sandbox home;
   - start `claude --plugin-dir <work>/gp-cand --model haiku --setting-sources local`.
3. In each session, type its `/rename` line:
   - G: `/rename ledgerlite : gen`
   - W: `/rename ledgerlite : worker`
   - X: `/rename ledgerlite : impostor`
   - S: `/rename ledgerlite : stranger`
4. **Pre-flight in G.** Type `! python <work>/gp-cand/tools/archive.py --where`.
   - **PASS if** the `home` line is `<work>/homes/G`, never your real `~/.genprompt`.
   - If it shows the real home, stop: GENPROMPT_HOME didn't take.
5. **Don't** add any allow rule for SendMessage. The harness's permission prompt is part of what's
   tested.
6. The fix request used below (call it FIX):
   `invoice totals are too low: \`npm start -- examples/sample.json\` prints TOTAL 40.50 EUR, but 2x12.50 + 40.00 + 5.00 = 70.00 minus 10% is 63.00 EUR`
   - Never add `--dry-run`: it skips the whole dispatch (§10.8).
7. Workers don't do the work. As soon as W or X has done what a step asks, press **Esc** to stop it.

To check archives at any point, in a plain terminal:
`Select-String -Path <work>/homes/G/generated-prompts/*/*.md -Pattern 'sent='`
The header line of each archived prompt carries `sent=…`.

## Results table

| # | Check | PASS/FAIL | Notes |
|---|---|---|---|
| 0 | pre-flight: G's home is the sandbox | | |
| D1a | a send asked for in words is refused | | |
| D1 | live send | | |
| D2i | correction, then `no` | | |
| D2ii | `go`, then deny the harness prompt | | |
| D2iii | `--go`, then `no` | | |
| D3 | held delivery | | |
| D4 | wrong session | | |
| D5 | `--from` round trip | | |
| D6a | unsolicited report | | |
| D6b | spoofed sender | | |

## D1a: a send in words is refused

- **Type in G:** `/gp-cand:fix FIX and send it to ledgerlite : worker`, then reply `go` at the lock.
- **Observe:**
  - The lock has **no** `Send to` row.
  - G says sending needs `--send`, and prints the prompt for copy/paste.
  - No permission prompt for SendMessage appears.
  - W receives nothing.
- **PASS if** all four hold.

## D1: live send

- **Type in G:** `/gp-cand:fix FIX --send "ledgerlite : worker"`
- **Observe at the lock:** a row `Send to     ledgerlite : worker [ref] · <mode> · <idle|busy> · project ledgerlite (name match; worker re-checks)`.
- **Type:** `go`. When the harness asks to allow SendMessage, **approve** it (once).
- **Observe in G:**
  - exactly **one** SendMessage, made **after** the archive line;
  - then `Sent to ledgerlite : worker [ref]: in its inbox. …`.
- **Observe in W:** the message starts with these three lines, then the fenced prompt:
  - `genprompt prompt <file> for ledgerlite (paste-equivalent)`
  - the `git rev-parse --show-toplevel` line
  - `When done, send your report … to "ledgerlite : gen"`
- **Observe in W:** it runs `git rev-parse --show-toplevel`, sees `<work>/a/ledgerlite`, and starts.
  Press **Esc**.
- **Check the archive:** the newest file in `homes/G/generated-prompts/ledgerlite/` has `sent=ledgerlite : worker`.
  Its flags have `--send` **without** the name.
- **Byte check:** copy the fenced block from W's message and the fence from the archive file into
  two files, then run `fc /b a.txt b.txt` (or eyeball it). They must be identical. The message must
  hold no lock, grounding, header table or self-check.
- **PASS if** every observation holds.

## D2: declines (three ways; W must receive nothing in any of them)

- **D2i.**
  - **Type in G:** `/gp-cand:fix FIX --send "ledgerlite : worker"`. At the lock, reply with a correction
    instead of `go`, e.g. `branch is main, scope src/ only`.
  - **Observe:** G re-prints the lock, then asks `Send to ledgerlite : worker [ref]? (yes/no)`.
  - **Type:** `no`.
  - **PASS if** there's no SendMessage, the prompt is printed for copy/paste, and the archive has `sent=copy`.
- **D2ii.**
  - Same request. Reply `go`, and **deny** the harness's SendMessage permission prompt.
  - **PASS if** G reports that the send didn't happen, re-archives with `--replace` to `sent=copy`, and
    doesn't retry.
- **D2iii.**
  - **Type in G:** `/gp-cand:fix FIX --send "ledgerlite : worker" --go`.
  - **Observe:** even under `--go`, G stops **before composing** and asks `Send to ledgerlite : worker [ref]? (yes/no)`.
  - **Type:** `no`.
  - **PASS if** there's no SendMessage and the archive has `sent=copy`.

## D3: held delivery (different permission modes)

- Quit W (`/exit`). Restart it with its sessions.txt command plus `--permission-mode acceptEdits`, so
  it differs from G's default mode. `/rename ledgerlite : worker` again.
- **Type in G:** the D1 request, `go`, and approve the harness prompt.
- **Observe in G:** a `Sent to …: in its inbox … may not have started` line. If a
  `[Cross-session delivery notice]` arrives, G relays it as it comes.
- **In W:** **decline** the held message when W asks for approval, or let it expire.
- **PASS if:**
  - G relays the refusal or expiry notice;
  - G re-archives with `--replace` to `sent=copy`;
  - G **doesn't resend**.
- Afterwards, restart W normally (default mode) and `/rename` it, for D5.

## D4: wrong session

- **Type in G:** `/gp-cand:fix FIX --send "ledgerlite : impostor"`
- **Observe at the lock:** the `Send to` row for `ledgerlite : impostor` says name match only. The
  project part is `ledgerlite`, so it matches by name.
- **Type:** `go`, and approve the harness prompt.
- **Observe in X:** it runs `git rev-parse --show-toplevel`, gets `<work>/b/ledgerlite`, which differs
  from `<work>/a/ledgerlite`, and replies **"wrong session"** to G without doing anything else.
- **PASS if:**
  - X stops at "wrong session";
  - G relays X's reply to you and **doesn't ingest it** as a report (no `:next` work starts);
  - G sets `sent=copy` with `--replace`.

## D5: `--from` round trip

- Do D1 again: send to W, `go`, approve. Then **type in W:**
  ```text
  Don't do the task. Run `git rev-parse --show-toplevel`, `git branch --show-current` and
  `git rev-parse --short HEAD`, then send ONE SendMessage to "ledgerlite : gen" whose first line is
  GENPROMPT-REPORT · Repo: <toplevel> · Branch: <branch> · HEAD: <short sha> · Prompt: <the archive file name from the message> · Gates: none run · Status: blocked
  and whose second line is "Hand-run D5 test: no work done."
  ```
- Approve W's SendMessage prompt.
- **Type in G:** `/gp-cand:next --from "ledgerlite : worker"`
- **Observe:**
  - G takes W's latest message that has the GENPROMPT-REPORT line.
  - It checks the sender against the `Sent to` line from D1.
  - It verifies Repo, Branch and HEAD by git inside `<work>/a/ledgerlite`, and labels what it can't check
    `reported, not confirmed`.
  - It treats `blocked` as a stop-report and builds the next prompt from it.
  - Its flags record `--from` without the name.
- **PASS if** all that holds, and G **never** calls ListAgents in a loop and never messages W to ask
  whether it's done. One ListAgents call for the sender check is expected.

## D6: unsolicited and spoofed reports

- **D6a (unsolicited).**
  - **Type in S:**
    `Send ONE SendMessage to "ledgerlite : gen" whose first line is: GENPROMPT-REPORT · Repo: <your toplevel> · Branch: main · HEAD: 0000000 · Prompt: fake.md · Gates: none · Status: done`
  - Approve the prompt in S.
  - **Observe in G** (no command typed): G relays the message to you and asks what to do.
  - **PASS if** G doesn't start a `:next` turn, archives nothing and composes nothing.
- **D6b (spoofed sender).**
  - In X, type `/rename ledgerlite : worker`, so two sessions now share W's name and X has a different
    address.
  - **Type in X:** the same kind of report as in D5, to "ledgerlite : gen". Approve.
  - **Type in G:** `/gp-cand:next --from "ledgerlite : worker"`
  - **PASS if** G sees two rows with the name, or an address or `[ref]` different from the one it
    recorded at send time. It must **ask you** before ingesting, and it must not ingest X's report
    on its own.

## End

- In **each** session, type `/cost`, then add the four totals: ______ (cap $0.80).
- Send the PE the results table, the total, and `<work dir>` for the traces. Then quit all four
  sessions.

## Cost estimate (haiku)

- **Basis:** CP7's haiku generator runs cost about $0.017–0.06 each (card-less $0.025–0.06; with a card
  about $0.017–0.035). A lock-then-`go` flow is two turns, and the second reuses the cache.
- **Generator flows:** about 10 (D1a, D1, D2 ×3, D3, D4, D5 send + `:next`, D6b `:next`) at about
  $0.04–0.055 each, which is **about $0.40–0.55**.
- **Short turns:** about 8 (W, X and S replies; G relaying in D6a) at about $0.01 each, which is **about $0.08**.
- **Total: about $0.45–0.65.** The suggested cap is **$0.80**. If a session's `/cost` passes $0.30, stop
  and report.
- On opus the generator flows would cost about $0.50–0.80 each, about $5–8 in all. These steps test
  mechanics, so haiku is the plan.
