# Utility: `/genprompt:help`

Emits no worker prompt. Writes nothing. Needs no TARGET LOCK.

**With no argument:** print, compactly:
1. the two-chat loop in 3 lines (generator → prompt → worker → stop-report → `:next`)
2. the picker table from `archetypes/README.md` ("I want to…" → command)
3. the utilities and modifiers from `guide/08-grammar.md`
4. the common lifecycles line

**With a goal** (`/genprompt:help I need to move from Drizzle to Supabase`):
1. match the goal against the picker, and recommend **one** command (or an honest hybrid) with a
   one-line reason
2. show the exact invocation to type, with the flags that fit (`--repo`, `--unattended`, …)
3. if two archetypes are close, name the runner-up and the deciding question

Never start generating a prompt from `:help`. The user runs the recommended command.
