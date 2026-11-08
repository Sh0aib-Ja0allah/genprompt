# Gate ladder: Rust

The labels `(script)`, `(contract)` and `(derived)`, the provenance rule for a derived
command and the workspace step are in `stacks/stack-matrix.md` section 3.
First hit wins in each cell.

- Rust: `cargo fmt --check` · `cargo clippy -- -D warnings` · `cargo test` · `cargo build` (a Cargo
  workspace adds `-p <crate>` or `--workspace`, per `stacks/workspaces.md`)
