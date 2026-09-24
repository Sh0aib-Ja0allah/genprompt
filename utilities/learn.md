# Utility: `/genprompt:learn <rule or lesson>`

The §12 fold-back loop. It emits no worker prompt. **This is the only command that may edit
`~/.genprompt/local-rules.md`**, and only after showing the diff. It never edits the genprompt root
(the plugin): a plugin update would erase the change, and the root is read-only at runtime.

1. **Restate the lesson** as one transferable rule: general, not tied to one repo's names. If the
   input is tied to a specific repo, generalise it, and keep the original as a one-line example
   *pattern*, not specifics.
2. **Check the suite first.** Grep the genprompt root for a rule that already covers it. If one
   does, say where (`file:line`) and stop, or propose a narrower amendment. Also Read
   `~/.genprompt/local-rules.md` if it exists, and prefer amending a personal rule over adding a
   near-duplicate.
3. **Place it** under the heading that matches the §12 map in `guide/00-index.md`. Use these
   headings in `local-rules.md`, creating one only when it is first needed:
   - `## Blocks (§4)`: a mechanism or a missing block
   - `## Anti-patterns (§7)`: a class of mistake
   - `## Environment facts (§11)`: a fact about this machine (a tool off PATH, a memory flag)
   - `## Archetypes (§5)`: a recurring shape, or an amendment to one archetype
   - `## Stacks and gates`: a stack or gate fact
   A new file starts with the line `# genprompt personal rules` and one line saying these rules add
   to the suite and win over it for this user.
4. **Show the exact diff**: the file, the heading, the new text, and the date. Each rule is one
   bullet that ends with `(learned <YYYY-MM-DD>)`.
5. **Wait for "yes".** Then apply it with Write or Edit. Resolve `~` to the absolute home directory
   first (`ls -d ~`).
6. **Offer it upstream** when the rule would help every user of genprompt, not just this machine.
   Print a ready-to-paste issue for the genprompt repository: a title, the rule, where it belongs in
   the suite (the file and the section), and one anonymised example. Never include repo names,
   paths or code from the user's projects in that issue.
7. **Never renumber sections or re-letter archetypes**, even in a personal rule. Refer to the
   suite's existing numbers.
