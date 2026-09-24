## 11. Environment facts

> Environment facts describe a **machine**, not a repo. There are two kinds:
> - **General facts** about Claude Code's tools on a given OS: listed below.
> - **Your machine's facts**, such as a tool that is installed but off PATH, a required memory flag,
>   or what runs under Docker. These live in `~/.genprompt/local-rules.md` under
>   `## Environment facts (§11)`. Add one with `/genprompt:learn`.
>
> Include a fact in a prompt only when the worker will hit it. When a fact matters, put it in a
> §4.22 verify-at-start block, because a machine can change.

### Any OS

- **Check before declaring a tool missing.** A tool can be installed but off PATH: a `.phar`, a
  version-manager shim, or a binary bundled with an app. A worker once checked PATH, concluded
  Composer was absent, and gated six workstreams on it. When a gate depends on such a tool, the
  prompt names how to find it (`<tool> --version`, then the known install location from
  `local-rules.md`) and never lets "not on PATH" mean "not installed".
- **Some PHP/Laravel gates need `php -d memory_limit=512M`.** A gate that dies at 128M is an
  environment limit, not a test failure.
- **Prefer forward slashes in Bash-tool commands.** They work on every OS.

### Windows

- **Two shells.** The Bash tool is Git Bash (POSIX). The PowerShell tool is often Windows
  PowerShell **5.1**: no `&&`/`||`, no ternary, no `??`; use `A; if ($?) { B }`. Do not assume
  `pwsh` (7+) exists; check for it.
- **`~` is not expanded in PowerShell 5.1 native-command arguments.** Give absolute paths.
- **PowerShell here-strings (`@'…'@`) do not work inside the Bash tool.** The `@` concatenates
  literally and mangles a commit subject. Use a heredoc.
- **`docker compose exec` through the Bash tool needs `MSYS_NO_PATHCONV=1`**, or Git Bash rewrites
  container paths.
- **Line endings.** With `core.autocrlf` on, check how the repo stores a file before diagnosing a
  whitespace-only diff.

---
