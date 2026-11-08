# Gate ladder: Terraform

The labels `(script)`, `(contract)` and `(derived)`, the provenance rule for a derived
command and the workspace step are in `stacks/stack-matrix.md` section 3.
First hit wins in each cell.

| Gate | Command |
|---|---|
| format | `terraform fmt -check -recursive` (derived: built in) |
| validate | `terraform init -backend=false` then `terraform validate`: `-backend=false` downloads providers but never touches remote state |
| lint | `tflint` only if `.tflint.hcl` exists and tflint is proven present |
| plan | `terraform plan` is not a default gate: it reads remote state and needs cloud credentials. Emit it only when the contract or CI names it, as read-only evidence, with its credential needs stated |
| ⚠ destructive | `terraform apply`, `terraform destroy`, `terraform import`, `terraform state rm`/`mv`, `terraform force-unlock`: never a gate. Always ⚠, run only by the user, after a reviewed plan |
