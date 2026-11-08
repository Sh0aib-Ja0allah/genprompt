# Gate ladder: Node (the package manager `<pm>` comes from the lockfile)

The labels `(script)`, `(contract)` and `(derived)`, the provenance rule for a derived
command and the workspace step are in `stacks/stack-matrix.md` section 3.
First hit wins in each cell.

| Gate | Command |
|---|---|
| format | `<pm> run format:check` / `format` (script) → `<pm> exec prettier --check .` if prettier is a dependency and has a config |
| lint | `<pm> run lint` (script) → `<pm> exec eslint .` if eslint is a dependency and has a config |
| typecheck | `typecheck` / `type-check` / `tsc` (script) → `<pm> exec tsc --noEmit` if a `tsconfig.json` exists and typescript is a dependency |
| test | `<pm> test` / `<pm> run test` (script) → `<pm> exec vitest run` or `jest` if it is a dependency and a test file exists |
| build | `<pm> run build` (script) |
| smoke / e2e | `test:e2e` / `e2e` (script), `playwright test` if configured, `.maestro/*.yaml`, `scripts/smoke-*` |
