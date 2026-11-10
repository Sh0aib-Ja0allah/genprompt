# Utility: `/genprompt:help`

Emits no worker prompt. Writes nothing. Needs no TARGET LOCK.

With no argument: print, compactly:
1. the two-chat loop in 3 lines (generator → prompt → worker → stop-report → `:next`)
2. first, `/genprompt:auto <what you want>` (it picks the command), then the six core commands
   from the picker's Core table (`:slice`, `:fix`, `:commit`, `:approve`, `:redesign`, `:next`),
   each with its purpose
3. the picker's Occasional table from `archetypes/README.md` ("I want to…" → command)
4. the utilities and modifiers from `guide/08-grammar.md`
5. the common lifecycles line

Wherever you show `--send <session>` or `:next --from <session>`, mark it EXPERIMENTAL (its
hand-run checks follow after 1.3.0), and never recommend either as the default path.

With a goal (`/genprompt:help I need to move from Drizzle to Supabase`):
1. match the goal against the picker, and recommend one command (or an honest hybrid) with a
   one-line reason
2. show the exact invocation to type, with the flags that fit (`--repo`, `--unattended`, …)
3. if two archetypes are close, name the runner-up and the deciding question
4. end with the exact `:auto` line to run, the goal and flags filled in:
   `/genprompt:auto <the goal> <flags>`

The continue path (route these without asking, because they are the most common follow-ups):
- a worker's stop-report arrived → `/genprompt:next` with the report pasted (pasting the report
  alone, with no command, means the same)
- the report has findings or open questions that need your decision first → `/genprompt:approve`
  with the rulings, or `:next` and say so (it becomes `J+E`)
- a prompt already sent to the worker needs a change → `/genprompt:approve amend <prior prompt>`
- the worker lost its context mid-slice → `/genprompt:resume`

Don't start generating a prompt from `:help`: the user runs the recommended command.
