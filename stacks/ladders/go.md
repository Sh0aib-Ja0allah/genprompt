# Gate ladder: Go

The labels `(script)`, `(contract)` and `(derived)`, the provenance rule for a derived
command and the workspace step are in `stacks/stack-matrix.md` section 3.
First hit wins in each cell.

| Gate | Command |
|---|---|
| format | `gofmt -l .` must print nothing |
| lint | `go vet ./...` → `golangci-lint run` if `.golangci.y*ml` exists |
| typecheck / build | `go build ./...` |
| test | `go test ./...` if `*_test.go` files exist |
