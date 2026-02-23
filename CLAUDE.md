# CLAUDE.md — Development Rules

## Pull Request Policy

**Never push directly to `main`.** All changes must go through a Pull Request.

1. Create a feature branch: `git checkout -b <type>/<short-description>`
2. Commit changes on the branch
3. Push the branch and open a PR via `gh pr create`
4. Do not merge without review

Branch naming convention:
- `fix/<description>` — bug fixes
- `feat/<description>` — new features
- `docs/<description>` — documentation-only changes
- `chore/<description>` — maintenance, refactoring
