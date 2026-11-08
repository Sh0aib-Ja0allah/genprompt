# Gate ladder: C/C++ (CMake; the build dir is the one the presets or CI use, `build/` otherwise)

The labels `(script)`, `(contract)` and `(derived)`, the provenance rule for a derived
command and the workspace step are in `stacks/stack-matrix.md` section 3.
First hit wins in each cell.

| Gate | Command |
|---|---|
| configure | `cmake --preset <preset>` if `CMakePresets.json` names one → `cmake -S . -B build` |
| build | `cmake --build --preset <preset>` → `cmake --build build` |
| format | `clang-format --dry-run --Werror <files>` only if `.clang-format` exists and clang-format is proven present (a verify-at-start check; it does not ship with CMake) |
| lint | `clang-tidy -p build <files>` only if `.clang-tidy` exists and the configure step exports `compile_commands.json` |
| test | `ctest --preset <preset>` → `ctest --test-dir build --output-on-failure`, only if `enable_testing()` / `add_test(` exists |
