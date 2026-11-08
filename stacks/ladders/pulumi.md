# Gate ladder: Pulumi

The labels `(script)`, `(contract)` and `(derived)`, the provenance rule for a derived
command and the workspace step are in `stacks/stack-matrix.md` section 3.
First hit wins in each cell.

| Gate | Command |
|---|---|
| format / lint / typecheck / test | the program language's own ladder (the `node.md`, `python.md`, `go.md` or `dotnet.md` ladder), run in the program dir |
| preview | `pulumi preview --stack <stack>` is not a default gate: it reads the stack's state and needs credentials. Emit it only when the contract or CI names it, as read-only evidence |
| ⚠ destructive | `pulumi up`, `pulumi destroy`, `pulumi refresh --yes`, `pulumi state delete`, `pulumi cancel`: never a gate. Always ⚠, run only by the user |
