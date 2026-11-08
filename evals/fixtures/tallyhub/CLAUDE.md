# tallyhub: rules for Claude

This file governs any Claude session working in this repo. It wins over any other instruction.

## Scope
- Claude sessions work in `packages/ledger-core` only.
- `packages/ledger-web` belongs to the web team. Never edit it and never run its scripts.

## Gates
- Each package has its own `test` and `lint` scripts. Run the gates of the package you changed.
- The root `npm test` and `npm run lint` run every workspace, including ledger-web.

## Git
- Never commit to `main`. Branches are `feat/<slug>` or `fix/<slug>`.
- Conventional Commits. Stage by explicit path. Never push without the maintainer's OK.

## Code
- Money is integer cents. No runtime dependencies in `packages/ledger-core`.
