# Gate ladder: PHP / Laravel (Composer may not be on PATH; see `guide/07-environment.md`)

The labels `(script)`, `(contract)` and `(derived)`, the provenance rule for a derived
command and the workspace step are in `stacks/stack-matrix.md` section 3.
First hit wins in each cell.

| Gate | Command |
|---|---|
| format | `composer run <format-script>` (script) → `vendor/bin/pint --test` if `laravel/pint` is in require-dev (zero-config) |
| lint / static | `vendor/bin/phpstan analyse` if phpstan or larastan is present with a config |
| typecheck | – |
| test | `composer test` (script) → `php artisan test` (Laravel) → `vendor/bin/pest` / `vendor/bin/phpunit` if present |
| build | the asset build from the Node side of the same root (`<pm> run build`), if one exists |
| smoke | `php artisan route:list` count; a `tests/Browser` Dusk suite if present |
| ⚠ destructive | `migrate:fresh`, `migrate:refresh`, `migrate:reset`, `migrate:rollback`, `db:wipe`, and every variant the contract warns about (e.g. `--env=testing` with no `.env.testing` hits the dev DB): always ⚠, always behind confirmation, and quote the contract's guard |
