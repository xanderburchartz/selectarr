# Contributing to Selectarr

Thanks for taking the time to contribute. This document covers bug reports, feature requests, and pull requests.

## Bug reports

Before opening a new issue, search [existing issues](https://github.com/xanderburchartz/selectarr/issues) to avoid duplicates.

A good bug report includes:

- **Selectarr version** (shown in the bottom-left of the sidebar)
- **How you're running it** — Docker or local Python, and the OS/platform
- **Steps to reproduce** — the exact sequence of actions that triggers the bug
- **What you expected** vs **what actually happened**
- **Relevant logs** — `docker compose logs selectarr` or the terminal output

Use the [Bug report](.github/ISSUE_TEMPLATE/bug_report.md) issue template.

## Feature requests

Open a [Feature request](.github/ISSUE_TEMPLATE/feature_request.md) issue and describe:

- The problem you're trying to solve
- The solution you have in mind
- Any alternatives you've considered

Features are more likely to be accepted if they fit the existing scope: manual, deliberate media cleanup with Jellyfin watch-status awareness.

## Pull requests

1. **Open an issue first** for anything beyond a small bug fix, so we can discuss the approach before you invest time writing code.

2. **Fork the repository** and create a branch from `main`:
   ```bash
   git checkout -b fix/short-description
   ```

3. **Set up the development environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp config.yaml.example config/config.yaml  # fill in your values
   uvicorn app.main:app --reload --port 8889
   ```

4. **Keep changes focused.** One bug fix or feature per PR — avoid bundling unrelated changes.

5. **Test your changes** against a real Jellyfin/Radarr/Sonarr/Lidarr setup if possible. Dry-run mode is always safe to test with.

6. **Update documentation** if your change affects behaviour described in `README.md` or `INSTALL.md`.

7. **Write a clear PR description** explaining what changed and why.

## Code style

- Python: follow the existing style (no enforced formatter yet — just keep it consistent)
- Templates: Jinja2 + HTMX, no JavaScript framework
- Keep imports, routes, and service methods in the same pattern as existing files

## Licence

By contributing you agree that your contributions will be licensed under the [MIT Licence](LICENSE).
