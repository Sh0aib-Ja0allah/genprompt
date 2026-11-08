# Gate ladder: Python (the prefix `<run>` comes from the lockfile: `uv run`, `poetry run`, `pipenv run`, or nothing)

The labels `(script)`, `(contract)` and `(derived)`, the provenance rule for a derived
command and the workspace step are in `stacks/stack-matrix.md` section 3.
First hit wins in each cell.

| Gate | Command |
|---|---|
| format | `<run> ruff format --check .` if ruff is configured → `<run> black --check .` |
| lint | `<run> ruff check .` → `<run> flake8` |
| typecheck | `<run> mypy .` or `<run> pyright` if configured |
| test | `<run> pytest` if tests exist → `python manage.py test` (Django) |
