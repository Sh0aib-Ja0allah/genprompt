# Workspaces and monorepo orchestrators

Read this file only when the repo has more than one manifest directory or a workspace file. It
extends `stacks/stack-matrix.md` (detection, labels and the per-stack gate ladders live there).

A workspace is one repository with several packages and, usually, one tool that runs a task across
them. Detect it before deriving gates, because the right gate for a slice depends on which package
is in scope.

| Orchestrator | Evidence file (read it; never assume) | Package list from |
|---|---|---|
| pnpm workspaces | `pnpm-workspace.yaml` | its `packages:` globs |
| Yarn workspaces | root `package.json` `"workspaces"` + `yarn.lock` | the `workspaces` globs (or `workspaces.packages`) |
| npm workspaces | root `package.json` `"workspaces"` + `package-lock.json` | the `workspaces` globs |
| Bun workspaces | root `package.json` `"workspaces"` + `bun.lock` | the `workspaces` globs |
| Turborepo | `turbo.json` (on top of one of the above) | the package manager's list; tasks from `turbo.json` `tasks` (`pipeline` in Turborepo 1.x) |
| Nx | `nx.json`, plus `project.json` per project or `nx` targets in `package.json` | `project.json` files; targets from them and `nx.json` `targetDefaults` |
| Cargo workspace | root `Cargo.toml` with `[workspace]` | `members` (minus `exclude`) |
| Go workspace | `go.work` | its `use` directives |
| Elixir umbrella | root `mix.exs` with `apps_path` | the `apps/*` directories |

How to derive a gate for each command, in this order:
1. **The contract wins.** If `CLAUDE.md`/`AGENTS.md` names the command to run (for example "always
   run `pnpm turbo run test` from the root"), emit exactly that, labelled `(contract)`.
2. One package is in scope, and it has its own script for the gate: run that package's script
   through the package manager's filter, labelled `(script)`, with the package's `package.json` as
   evidence. Node-style: `pnpm --filter <pkg> run <script>` · `yarn workspace <pkg> run <script>` ·
   `npm run <script> -w <pkg>` · `bun run --filter <pkg> <script>`.
3. The task is defined in the orchestrator, not in the package: run the orchestrator, scoped to the
   package, labelled `(script)`, with `turbo.json` or `project.json` as evidence. Turborepo:
   `<pm> exec turbo run <task> --filter=<pkg>` · Nx: `<pm> exec nx run <project>:<target>`.
4. Several packages are in scope, or the work changes a shared package: run the orchestrator across
   the workspace, labelled `(script)`: the root script if one exists (`<pm> run test` that calls
   `turbo run test`), otherwise `<pm> exec turbo run <task>` or `<pm> exec nx run-many -t <target>`.
   Use `--filter=...<pkg>` (Turborepo) or `nx affected -t <target>` only when the repo's CI or
   contract already does; say which.
5. Non-Node workspaces: Cargo `cargo test -p <crate>` for one crate, `cargo test --workspace` for
   several (same for `clippy`, `build`, `fmt --all --check`) · Go `go test ./<module>/...` per module
   listed in `go.work` · Elixir umbrella `mix test` from the root, or `mix cmd --app <app> mix test`
   for one app.

Name the in-scope packages and the out-of-scope ones in the lock's `Scope` line, and keep a gate
inside the scope it claims to check: a per-package filter never stands in for a workspace-wide
check that the contract or CI requires.
