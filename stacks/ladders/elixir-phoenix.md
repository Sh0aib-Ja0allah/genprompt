# Gate ladder: Elixir / Phoenix

The labels `(script)`, `(contract)` and `(derived)`, the provenance rule for a derived
command and the workspace step are in `stacks/stack-matrix.md` section 3.
First hit wins in each cell.

| Gate | Command |
|---|---|
| format | `mix format --check-formatted` (derived: built in; uses `.formatter.exs`) |
| lint | `mix credo --strict` only if `:credo` is a dependency |
| typecheck / build | `mix compile --warnings-as-errors` only if the repo or CI already compiles that way → otherwise `mix compile`; `mix dialyzer` only if `:dialyxir` is a dependency (slow: name it, do not make it the default gate) |
| test | `mix test` if `test/` has tests (Phoenix with Ecto needs the test database the contract describes) |
| smoke | `mix phx.routes` count (Phoenix) |
| ⚠ destructive | `mix ecto.reset`, `mix ecto.drop`, `mix ecto.rollback`, `mix ecto.migrate` against a non-test database: always ⚠, always behind confirmation |
