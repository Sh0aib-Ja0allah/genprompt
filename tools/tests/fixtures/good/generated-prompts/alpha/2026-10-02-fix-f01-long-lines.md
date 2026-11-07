<!-- genprompt v3: key=alpha | repo=alpha | path=<path> | date=2026-10-02 | archetype=L | follows=- -->

# Fixture: a short prompt in long lines

````text
Repo: the fixture repo, branch main. This paragraph is one physical line on purpose: some generators write each part of the prompt as a single long line, so the block has few lines but plenty of content, and doctor must count it by width (ceil of length over 100), not as a stub.
NOW: fix F01. This paragraph is one physical line on purpose: some generators write each part of the prompt as a single long line, so the block has few lines but plenty of content, and doctor must count it by width (ceil of length over 100), not as a stub.
GATE: npm test (script). This paragraph is one physical line on purpose: some generators write each part of the prompt as a single long line, so the block has few lines but plenty of content, and doctor must count it by width (ceil of length over 100), not as a stub.
WHAT YOU CANNOT DO: push. This paragraph is one physical line on purpose: some generators write each part of the prompt as a single long line, so the block has few lines but plenty of content, and doctor must count it by width (ceil of length over 100), not as a stub.
REPORT: a GENPROMPT-REPORT line, then the gates. This paragraph is one physical line on purpose: some generators write each part of the prompt as a single long line, so the block has few lines but plenty of content, and doctor must count it by width (ceil of length over 100), not as a stub.
Start now.
````

| # | Item | Verdict | Reason |
|---|---|---|---|
| 1 | Target resolved | PASS | fixture |
