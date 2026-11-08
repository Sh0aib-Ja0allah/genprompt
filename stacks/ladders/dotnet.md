# Gate ladder: .NET

The labels `(script)`, `(contract)` and `(derived)`, the provenance rule for a derived
command and the workspace step are in `stacks/stack-matrix.md` section 3.
First hit wins in each cell.

| Gate | Command |
|---|---|
| format | `dotnet format --verify-no-changes` |
| lint | `dotnet build -warnaserror` only if the repo already treats warnings as errors; otherwise – |
| typecheck / build | `dotnet build` |
| test | `dotnet test` only if a test project exists |
| smoke | – |
