# Gate ladder: Flutter / Dart

The labels `(script)`, `(contract)` and `(derived)`, the provenance rule for a derived
command and the workspace step are in `stacks/stack-matrix.md` section 3.
First hit wins in each cell.

| Gate | Command |
|---|---|
| codegen | `dart run build_runner build --delete-conflicting-outputs` if `build_runner` is a dev dependency (run before analyze and test) |
| format | `dart format --set-exit-if-changed .` |
| lint / typecheck | `flutter analyze` (`dart analyze` for a pure Dart package) |
| test | `flutter test` if `test/` has tests |
| build | `flutter build <apk\|appbundle\|ios\|web>`: the target is named by the contract or CI; otherwise ask |
| smoke | `flutter test integration_test/` if present |
