# Gate ladder: Bun

The labels `(script)`, `(contract)` and `(derived)`, the provenance rule for a derived
command and the workspace step are in `stacks/stack-matrix.md` section 3.
First hit wins in each cell.

| Gate | Command |
|---|---|
| format / lint / typecheck | the `package.json` scripts through `bun run <script>` (script); the derived fallbacks are the Node ones with `bunx` in place of `<pm> exec` |
| test | `bun run test` (script) → `bun test` (derived: built in, zero-config) only if `*.test.*` / `*.spec.*` files exist |
| build | `bun run build` (script) |
