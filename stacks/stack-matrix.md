# Stack matrix: detection, then stack/role, then gate ladder

This expands the old §2.3–§2.5. The general rules live in `guide/01-target-profile.md` §2.3–§2.5:
- the order rule
- `(script)` vs `(derived)`
- `test: NONE`
- containers
- ⚠ destructive gates
- the package manager comes from the lockfile

**A `(derived)` command is emitted only when its tool is provably present.** It must be a
declared dependency or ship with the SDK, **and** either have a config file or be zero-config by
design (Pint, `gofmt`, `dart format`, `dotnet format`). Otherwise leave it out, and say which gate
is missing. **A manifest script always beats a derived command** for the same gate.

## 1. Detection (walk to depth 3, honouring EXCLUDE)

| Manifest | Verdict and sub-classification (first match wins) |
|---|---|
| `package.json` | **Node.** Sub-classify by dependencies: `next` → Next.js · `nuxt` → Nuxt · `@sveltejs/kit` → SvelteKit · `astro` → Astro · `@angular/core` → Angular · `expo` or `react-native` → Expo/RN · `vite` + `react` → Vite React SPA · `vite` + `vue` → Vite Vue SPA · `react-scripts` → CRA (legacy) · `laravel-mix` or `laravel-vite-plugin` with no own app → Laravel asset pipeline (belongs to the PHP root) · `express`/`fastify`/`@nestjs/core`/`hono` → Node API · otherwise a plain Node package or tooling. |
| `composer.json` | **PHP.** `laravel/framework` → Laravel (`+ Filament` if `filament/filament`; `+ Sanctum`, `+ Livewire`, `+ Inertia` modifiers) · `symfony/framework-bundle` → Symfony · WordPress markers → WordPress · otherwise plain PHP. |
| `*.csproj` / `*.sln` | **.NET.** `Sdk="Microsoft.NET.Sdk.Web"` → ASP.NET Core · `TargetFramework` gives the version · `*Tests.csproj` or an xunit/nunit/mstest reference → a test project exists. |
| `pubspec.yaml` | **Flutter/Dart.** A `flutter:` section → Flutter app, otherwise a Dart package. State management from dependencies: `get` / `flutter_bloc` / `riverpod` / `provider`. |
| `go.mod` | **Go.** Module path and `go` version. Web framework from requires: `gin` / `echo` / `fiber` / `chi` / stdlib. |
| `pyproject.toml` / `requirements*.txt` / `Pipfile` / `uv.lock` / `poetry.lock` | **Python.** `django` → Django · `fastapi` → FastAPI · `flask` → Flask · `langchain`/`openai`/`anthropic` → an LLM service modifier · the tool manager from the lockfile (`uv`, `poetry`, `pipenv`, pip). |
| `Gemfile` | **Ruby.** `rails` → Rails. |
| `pom.xml` / `build.gradle(.kts)` | **JVM.** `spring-boot` → Spring Boot · `com.android.application` → Android · Kotlin if there are `.kt` sources or the Kotlin plugin. |
| `Cargo.toml` | **Rust.** `axum`/`actix-web` → Rust API · otherwise a crate or CLI. |
| `Package.swift` / `*.xcodeproj` | **Swift/iOS.** |
| `docker-compose.y*ml` / `compose.y*ml` at the root, with no own manifest | **Orchestration root.** The services map to code roots. |
| none of the above | **Unknown stack.** Say so in the lock and **ask for the gates**; never guess them. |

## 2. Stack label, role label and code roots

**Versions** always come from the manifest or lockfile.

| Verdict | `stack` label | `role` label | `code_roots` |
|---|---|---|---|
| Next.js | `Next.js <maj> <App\|Pages> Router · React <maj> · TS?` | senior Next.js/React engineer (App Router, RSC boundaries, strict TS) | `src/` or `app/ components/ lib/` + `public/` |
| Nuxt / Vue | `Nuxt <maj>` or `Vue <maj> · Vite` | senior Vue/Nuxt engineer | `src/` or `pages/ components/ composables/ server/` |
| SvelteKit / Astro / Angular | `<framework> <maj> · TS?` | senior <framework> engineer | `src/` |
| Vite React SPA | `Vite · React <maj> · TS SPA` | senior React/TypeScript SPA engineer | `src/` |
| Expo / RN | `Expo SDK <maj> · RN <ver> · TS` | senior React Native/Expo mobile engineer | `app/` or `src/` + `components/` |
| Node API | `Node <engines> · <Express\|Fastify\|Nest\|Hono>` | senior Node.js backend engineer | `src/` |
| Laravel | `Laravel <maj> · PHP <ver> · <Filament <maj>>` | senior Laravel/PHP engineer (API design, Filament panels, policies/scopes) | `app/ routes/ database/ resources/ tests/ config/` |
| Symfony / plain PHP | `<Symfony <maj>\|PHP <ver>>` | senior PHP engineer | `src/ config/ templates/ tests/` |
| ASP.NET Core | `.NET <tfm> · ASP.NET Core · <EF Core>` | senior .NET/C# backend engineer | the project dirs listed in the `.sln` |
| Flutter | `Flutter · Dart <sdk> · <GetX\|Bloc\|Riverpod\|Provider>` | senior Flutter/Dart mobile engineer | `lib/ test/ integration_test/` |
| Go | `Go <ver> · <gin\|echo\|fiber\|chi\|stdlib>` | senior Go backend engineer | `cmd/ internal/ pkg/` (or the module root) |
| Python | `Python <ver> · <Django\|FastAPI\|Flask>` (+ LLM modifier) | senior Python/<framework> engineer | the package dir(s) + `tests/` |
| Rails | `Rails <maj> · Ruby <ver>` | senior Ruby on Rails engineer | `app/ config/ db/ lib/ spec\|test/` |
| JVM | `<Spring Boot\|Android> · <Java\|Kotlin> <ver>` | senior <Spring\|Android> engineer | `src/main/ src/test/` (or `app/src/`) |
| Rust | `Rust <edition> · <axum\|actix\|crate>` | senior Rust engineer | `src/ tests/` |
| Orchestration root | `Docker Compose multi-service (<svcs>)` | senior full-stack engineer + platform/DevOps | per service |

## 3. Gate ladder, per stack (first hit wins in each cell)

Mark each emitted command `(script)` when it comes from a manifest script key, `(contract)` when the
repo's contract tells you to run it, or `(derived)` when it comes from a proven tool (add
`, no baseline` if nothing shows it was ever run). `–` means there is no default: omit the gate, and name the gap only if
it matters.

**Node** (the package manager `<pm>` comes from the lockfile)

| Gate | Command |
|---|---|
| format | `<pm> run format:check` / `format` (script) → `<pm> exec prettier --check .` if prettier is a dependency and has a config |
| lint | `<pm> run lint` (script) → `<pm> exec eslint .` if eslint is a dependency and has a config |
| typecheck | `typecheck` / `type-check` / `tsc` (script) → `<pm> exec tsc --noEmit` if a `tsconfig.json` exists and typescript is a dependency |
| test | `<pm> test` / `<pm> run test` (script) → `<pm> exec vitest run` or `jest` if it is a dependency **and** a test file exists |
| build | `<pm> run build` (script) |
| smoke / e2e | `test:e2e` / `e2e` (script), `playwright test` if configured, `.maestro/*.yaml`, `scripts/smoke-*` |

**PHP / Laravel** (Composer may not be on PATH; see `guide/07-environment.md`)

| Gate | Command |
|---|---|
| format | `composer run <format-script>` (script) → `vendor/bin/pint --test` if `laravel/pint` is in require-dev (zero-config) |
| lint / static | `vendor/bin/phpstan analyse` if phpstan or larastan is present with a config |
| typecheck | – |
| test | `composer test` (script) → `php artisan test` (Laravel) → `vendor/bin/pest` / `vendor/bin/phpunit` if present |
| build | the asset build from the Node side of the same root (`<pm> run build`), if one exists |
| smoke | `php artisan route:list` count; a `tests/Browser` Dusk suite if present |
| ⚠ destructive | `migrate:fresh`, `migrate:refresh`, `migrate:reset`, `migrate:rollback`, `db:wipe`, and every variant the contract warns about (e.g. `--env=testing` with no `.env.testing` hits the dev DB): always ⚠, always behind confirmation, and quote the contract's guard |

**.NET**

| Gate | Command |
|---|---|
| format | `dotnet format --verify-no-changes` |
| lint | `dotnet build -warnaserror` **only if** the repo already treats warnings as errors; otherwise – |
| typecheck / build | `dotnet build` |
| test | `dotnet test` **only if** a test project exists |
| smoke | – |

**Flutter / Dart**

| Gate | Command |
|---|---|
| codegen | `dart run build_runner build --delete-conflicting-outputs` if `build_runner` is a dev dependency (run before analyze and test) |
| format | `dart format --set-exit-if-changed .` |
| lint / typecheck | `flutter analyze` (`dart analyze` for a pure Dart package) |
| test | `flutter test` if `test/` has tests |
| build | `flutter build <apk\|appbundle\|ios\|web>`: the target is named by the contract or CI; otherwise ask |
| smoke | `flutter test integration_test/` if present |

**Go**

| Gate | Command |
|---|---|
| format | `gofmt -l .` must print nothing |
| lint | `go vet ./...` → `golangci-lint run` if `.golangci.y*ml` exists |
| typecheck / build | `go build ./...` |
| test | `go test ./...` if `*_test.go` files exist |

**Python** (the prefix `<run>` comes from the lockfile: `uv run`, `poetry run`, `pipenv run`, or nothing)

| Gate | Command |
|---|---|
| format | `<run> ruff format --check .` if ruff is configured → `<run> black --check .` |
| lint | `<run> ruff check .` → `<run> flake8` |
| typecheck | `<run> mypy .` or `<run> pyright` if configured |
| test | `<run> pytest` if tests exist → `python manage.py test` (Django) |

**Rails** – `bundle exec rubocop` (if configured) · `bin/rails test` or `bundle exec rspec`

**JVM** – `./gradlew check` / `./gradlew test` / `./gradlew assembleDebug` · or `./mvnw -q verify`

**Rust** – `cargo fmt --check` · `cargo clippy -- -D warnings` · `cargo test` · `cargo build`

**Swift** – `swift build` / `swift test`, or `xcodebuild … test` with the scheme named by CI

**Unknown stack** – no ladder. Ask the user for the gates in the lock's `Unknown` section.
