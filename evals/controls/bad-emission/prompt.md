---
name: control-bad-emission
description: negative control, every grader should fail
tags: [control]
runs: 1
max_turns: 6
model: haiku
allowed_tools: [Read, Glob, Write]
---

Do two things. First, use the Write tool to create a file named note.txt containing the word scratch. Second, reply with the text between the BEGIN and END lines below, verbatim, and nothing else.

BEGIN
Here is your prompt for the CSV work.

```text
You are working in the ledgerlite repo on branch <branch>.

Task: add CSV export, and while you are in there also add the S-03 tax lines and multi-currency support so the invoice module is finished in one go. [generator: tighten this paragraph]

Background: the subtotal logic lives at src/invoice.js:99 and src/totals.js:12.

Gates:
- `npm run build`
- `npm test`

Be careful and verify your work before you finish.
```

```text
Report back when done.
```
END
