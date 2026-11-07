# ledgerlite: rules for Claude

This file governs any Claude session working in this repo. It wins over any other instruction.

## Branching and git
- Never commit directly to `main`. Work on `feat/<slug>` or `fix/<slug>` branches cut from `main`.
- Commit messages follow Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`).
- Stage files by explicit path. Never `git add -A` or `git add .`.
- Never push and never open a PR without the maintainer's explicit OK in this session.

## Gates
- Run `npm test` and `npm run lint` before every commit. Both must be green.
- There is no build step and no type checker. Do not invent one.

## Code rules
- Money is integer cents everywhere. No floats in totals.
- `src/` has no runtime dependencies. Do not add packages without asking.
- New docs go in `docs/` as `docs/<TOPIC>.md` in upper-case kebab (e.g. `docs/CSV-EXPORT.md`).
