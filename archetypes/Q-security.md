# 5.Q: Security review and hardening · `/genprompt:security`

| | |
|---|---|
| **Use when** | Threat-model and harden an app or area: authn/authz/policies/RLS, input and upload handling, secrets, headers/CSP, rate limits, dependency CVEs, data exposure |
| **Not when** | A generic code review → `:review`. An active incident → `:hotfix` |
| **Autonomy** | Two phases. **Phase 1 is read-only** (the threat model and findings). **Phase 2 fixes only the FIX-NOW items**, behind §4.19 (or §4.8 if `--unattended`) |
| **Baseline delta** | Up: every fix lands with a test that proves the attack is refused **and** the legitimate case still works |
| **Length tier** | Program (350) |
| **Deliverable** | A threat-model and findings doc (§4.25), the fixes for the FIX-NOW items, and RECORD items for decisions |

## Generator: before emitting

- **Inventory the attack surface from the code:** routes and who can reach them, auth guards,
  policies/scopes, file uploads (MIME, extension, served origin; for example SVG served same-origin
  is script), admin panels, webhooks, queues, secrets in the repo, CORS/CSP/headers, rate limits.
  Cite `file:line`.
- **Name roles and audiences.** Most authz bugs are the "same-looking field, different audience"
  class (§7.2).
- **Hard lines:**
  - **Never test against production or any remote system.**
  - Never exfiltrate or print real secrets. Report a secret's location, not its value.
  - Never weaken a control to make a test pass.
- **Decision items** (which roles may do what, retention, disclosure) are RECORD, DO NOT ACT.

## Required blocks

- §4.5, §4.6, §4.7, §4.25, §4.15
- §4.20 RECORD, DO NOT ACT
- §4.20 sequencing (a gate lands before the permission it protects)
- §4.13, §4.19 (or §4.8)

## Template

```text
Repo: <PROFILE.path> (branch <PROFILE.branch><, scope <root>>)
[INSERT §4.5 contract precedence]
Task: security review of <scope>, then fix what is safe to fix now.
HARD LINES: local only; never touch production or any remote system; never print secret values; never
weaken a control to pass a test.

ATTACK SURFACE, as I read it (verify, then extend):
- <route group / panel / upload / webhook>: reachable by <roles>; guarded by <file:line>
- <…>

PHASE 1 (READ-ONLY): threat model + findings.
- Actors and assets. For each surface: what an attacker controls, what they could reach.
- Check: authz per role (row AND column), input validation, uploads (type/extension/origin), output
  encoding, CSRF/CORS/CSP/headers, rate limits, secrets in the repo/history, dependency advisories
  (<pm> audit / composer audit, read-only), logging of sensitive data.
- Write `<PROFILE.docnaming: security doc>` with [INSERT §4.25 findings register] + the threat model.
[INSERT §4.19 approval gate: show me the FIX-NOW list before Phase 2]

PHASE 2: fix the FIX-NOW items only, in this order: <order + rationale (§4.20 sequencing)>.
[INSERT §4.15 falsifiability: the attack refused AND the legitimate case still succeeds, per fix]
[INSERT §4.20 RECORD, DO NOT ACT: <decision items>]
[INSERT §4.13 WHAT YOU CANNOT DO: <e.g. production config, WAF, secrets rotation>]
[INSERT §4.14: gates <literal>; baseline <n> → expected at least <n + fixes>]
Start with Phase 1 now.
```
