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
design (Pint, `gofmt`, `dart format`, `dotnet format`, `deno fmt`, `mix format`, `terraform fmt`).
Otherwise leave it out, and say which gate is missing. A manifest script always beats a derived
command for the same gate.

## 1. Detection (walk to depth 3, honouring EXCLUDE)

Check the rows in order; the first match wins. Bun and Deno come before Node because a Bun or Deno
project can also carry a `package.json`.

| Manifest | Verdict and sub-classification |
|---|---|
| `bun.lock` / `bun.lockb` next to `package.json` | Bun. The runtime and package manager are Bun. Sub-classify the framework from `package.json` exactly as for Node (`next`, `hono`, `elysia` → Bun API, …). |
| `deno.json` / `deno.jsonc` | Deno. `fresh` in `imports` → Fresh · `hono` → Deno API · otherwise a Deno module or CLI. A `package.json` beside it is a Node-compat shim, not a second stack. |
| `package.json` | Node. Sub-classify by dependencies: `next` → Next.js · `nuxt` → Nuxt · `@sveltejs/kit` → SvelteKit · `astro` → Astro · `@angular/core` → Angular · `expo` or `react-native` → Expo/RN · `vite` + `react` → Vite React SPA · `vite` + `vue` → Vite Vue SPA · `react-scripts` → CRA (legacy) · `laravel-mix` or `laravel-vite-plugin` with no own app → Laravel asset pipeline (belongs to the PHP root) · `express`/`fastify`/`@nestjs/core`/`hono` → Node API · otherwise a plain Node package or tooling. |
| `composer.json` | PHP. `laravel/framework` → Laravel (`+ Filament` if `filament/filament`; `+ Sanctum`, `+ Livewire`, `+ Inertia` modifiers) · `symfony/framework-bundle` → Symfony · WordPress markers → WordPress · otherwise plain PHP. |
| `*.csproj` / `*.sln` | .NET. `Sdk="Microsoft.NET.Sdk.Web"` → ASP.NET Core · `TargetFramework` gives the version · `*Tests.csproj` or an xunit/nunit/mstest reference → a test project exists. |
| `pubspec.yaml` | Flutter/Dart. A `flutter:` section → Flutter app, otherwise a Dart package. State management from dependencies: `get` / `flutter_bloc` / `riverpod` / `provider`. |
| `go.mod` | Go. Module path and `go` version. Web framework from requires: `gin` / `echo` / `fiber` / `chi` / stdlib. |
| `pyproject.toml` / `requirements*.txt` / `Pipfile` / `uv.lock` / `poetry.lock` | Python. `django` → Django · `fastapi` → FastAPI · `flask` → Flask · `langchain`/`openai`/`anthropic` → an LLM service modifier · the tool manager from the lockfile (`uv`, `poetry`, `pipenv`, pip). |
| `Gemfile` | Ruby. `rails` → Rails. |
| `mix.exs` | Elixir. `:phoenix` in `deps` → Phoenix (`+ LiveView` if `:phoenix_live_view`; `+ Ecto` if `:ecto_sql`) · an `apps/` umbrella with its own `mix.exs` files → umbrella project (see `stacks/workspaces.md`) · otherwise an Elixir library or OTP app. |
| `pom.xml` / `build.gradle(.kts)` | JVM. `spring-boot` → Spring Boot · `com.android.application` → Android · Kotlin if there are `.kt` sources or the Kotlin plugin. |
| `Cargo.toml` | Rust. `axum`/`actix-web` → Rust API · a `[workspace]` table → Cargo workspace (see `stacks/workspaces.md`) · otherwise a crate or CLI. |
| `CMakeLists.txt` | C/C++ (CMake). The language from `project(... LANGUAGES ...)` or the source extensions · `CMakePresets.json` gives the configure and build presets · `enable_testing()` / `add_test(` → CTest tests exist. A bare `Makefile` with no `CMakeLists.txt` is not this row: read its targets and ask for the gates. |
| `Package.swift` / `*.xcodeproj` | Swift/iOS. |
| `*.tf` / `.terraform.lock.hcl` | Terraform (infrastructure as code). The provider set from `required_providers` · the backend from `terraform { backend ... }`. |
| `Pulumi.yaml` | Pulumi (infrastructure as code). The program language from `runtime:` (`nodejs`, `python`, `go`, `dotnet`), whose own manifest also gets its own row above. |
| `docker-compose.y*ml` / `compose.y*ml` at the root, with no own manifest | Orchestration root. The services map to code roots. |
| none of the above | Unknown stack. Say so in the lock and **ask for the gates; never guess them**. |

## 1b. Workspaces and monorepo orchestrators

Read `stacks/workspaces.md` only when the repo has more than one manifest directory or a workspace
file (pnpm-workspace.yaml, workspaces in package.json, turbo.json, nx.json, Cargo [workspace],
go.work, an umbrella). It detects the orchestrator and decides per-package vs orchestrator gates.

## 2. Stack label, role label and code roots

Versions always come from the manifest or lockfile.

| Verdict | `stack` label | `role` label | `code_roots` |
|---|---|---|---|
| Next.js | `Next.js <maj> <App\|Pages> Router · React <maj> · TS?` | senior Next.js/React engineer (App Router, RSC boundaries, strict TS) | `src/` or `app/ components/ lib/` + `public/` |
| Nuxt / Vue | `Nuxt <maj>` or `Vue <maj> · Vite` | senior Vue/Nuxt engineer | `src/` or `pages/ components/ composables/ server/` |
| SvelteKit / Astro / Angular | `<framework> <maj> · TS?` | senior <framework> engineer | `src/` |
| Vite React SPA | `Vite · React <maj> · TS SPA` | senior React/TypeScript SPA engineer | `src/` |
| Expo / RN | `Expo SDK <maj> · RN <ver> · TS` | senior React Native/Expo mobile engineer | `app/` or `src/` + `components/` |
| Node API | `Node <engines> · <Express\|Fastify\|Nest\|Hono>` | senior Node.js backend engineer | `src/` |
| Bun | `Bun <ver> · <framework\|API\|package> · TS?` | senior TypeScript engineer on the Bun runtime | `src/` (or the framework's dirs) |
| Deno | `Deno <ver> · <Fresh\|Hono\|module>` | senior TypeScript engineer on the Deno runtime | `src/` or `routes/ islands/` (Fresh) or the module root |
| Laravel | `Laravel <maj> · PHP <ver> · <Filament <maj>>` | senior Laravel/PHP engineer (API design, Filament panels, policies/scopes) | `app/ routes/ database/ resources/ tests/ config/` |
| Symfony / plain PHP | `<Symfony <maj>\|PHP <ver>>` | senior PHP engineer | `src/ config/ templates/ tests/` |
| ASP.NET Core | `.NET <tfm> · ASP.NET Core · <EF Core>` | senior .NET/C# backend engineer | the project dirs listed in the `.sln` |
| Flutter | `Flutter · Dart <sdk> · <GetX\|Bloc\|Riverpod\|Provider>` | senior Flutter/Dart mobile engineer | `lib/ test/ integration_test/` |
| Go | `Go <ver> · <gin\|echo\|fiber\|chi\|stdlib>` | senior Go backend engineer | `cmd/ internal/ pkg/` (or the module root) |
| Python | `Python <ver> · <Django\|FastAPI\|Flask>` (+ LLM modifier) | senior Python/<framework> engineer | the package dir(s) + `tests/` |
| Rails | `Rails <maj> · Ruby <ver>` | senior Ruby on Rails engineer | `app/ config/ db/ lib/ spec\|test/` |
| Elixir / Phoenix | `Elixir <ver> · OTP <ver> · <Phoenix <maj> (+ LiveView)\|library>` | senior Elixir/Phoenix engineer (OTP, Ecto, LiveView) | `lib/ test/ config/ priv/` (umbrella: `apps/<app>/`) |
| JVM | `<Spring Boot\|Android> · <Java\|Kotlin> <ver>` | senior <Spring\|Android> engineer | `src/main/ src/test/` (or `app/src/`) |
| Rust | `Rust <edition> · <axum\|actix\|crate>` | senior Rust engineer | `src/ tests/` (workspace: each member) |
| C/C++ (CMake) | `<C\|C++><std> · CMake <min> · <compiler if the presets pin one>` | senior C/C++ systems engineer (CMake, memory safety, tests in CTest) | `src/ include/ tests/` (from `add_executable`/`add_library` sources) |
| Terraform | `Terraform <required_version> · <providers> · <backend>` | senior infrastructure engineer (Terraform, least-privilege IAM, state safety) | the module dirs with `*.tf` |
| Pulumi | `Pulumi · <runtime> · <cloud providers>` | senior infrastructure engineer (Pulumi, state safety) | the program dir named in `Pulumi.yaml` |
| Orchestration root | `Docker Compose multi-service (<svcs>)` | senior full-stack engineer + platform/DevOps | per service |

## 3. Gate ladder, per stack (first hit wins in each cell)

Mark each emitted command `(script)` when it comes from a manifest script key, `(contract)` when the
repo's contract tells you to run it, or `(derived)` when it comes from a proven tool (add
`, no baseline` if nothing shows it was ever run). `–` means there is no default: omit the gate,
and name the gap only if it matters. In a workspace, apply `stacks/workspaces.md` first.

Read only the ladder file for the stack you detected (section 1). A monorepo reads one ladder
per in-scope code root.

| Stack | Ladder file |
|---|---|
| Node (Next.js, Nuxt/Vue, SvelteKit/Astro/Angular, Vite SPA, Expo/RN, Node API) | `stacks/ladders/node.md` |
| Bun | `stacks/ladders/bun.md` |
| Deno | `stacks/ladders/deno.md` |
| PHP (Laravel, Symfony, plain PHP) | `stacks/ladders/php-laravel.md` |
| .NET / ASP.NET Core | `stacks/ladders/dotnet.md` |
| Flutter / Dart | `stacks/ladders/flutter-dart.md` |
| Go | `stacks/ladders/go.md` |
| Python (Django, FastAPI, Flask) | `stacks/ladders/python.md` |
| Ruby / Rails | `stacks/ladders/rails.md` |
| Elixir / Phoenix | `stacks/ladders/elixir-phoenix.md` |
| JVM (Spring Boot, Android) | `stacks/ladders/jvm.md` |
| Rust | `stacks/ladders/rust.md` |
| C/C++ (CMake) | `stacks/ladders/cpp-cmake.md` |
| Swift / iOS | `stacks/ladders/swift.md` |
| Terraform | `stacks/ladders/terraform.md` |
| Pulumi | `stacks/ladders/pulumi.md` |
| Orchestration root | the ladders of its services' stacks |

### Unknown stack

No ladder. Ask the user for the gates in the lock's `Unknown` section.
