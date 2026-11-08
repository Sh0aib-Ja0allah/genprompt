# Gate ladder: Deno

The labels `(script)`, `(contract)` and `(derived)`, the provenance rule for a derived
command and the workspace step are in `stacks/stack-matrix.md` section 3.
First hit wins in each cell.

| Gate | Command |
|---|---|
| format | `deno task fmt` (script, from `deno.json` `tasks`) → `deno fmt --check` (derived: built in) |
| lint | `deno task lint` (script) → `deno lint` (derived: built in) |
| typecheck | `deno task check` (script) → `deno check <entry>` with the entry named in `deno.json` (`exports` or the main task) |
| test | `deno task test` (script) → `deno test` (derived) only if `*_test.ts` / `*.test.ts` files exist; add the `--allow-*` permissions the existing tasks use, never `-A` on your own |
| build | `deno task build` (script) |
