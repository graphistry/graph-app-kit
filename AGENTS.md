# Agent Instructions

Guidance for AI coding agents working in this repository. Human contributors: see `DEVELOP.md`.

## Layout

- `src/python/` — Streamlit app: `views/<view>/` (one dashboard each), `components/`, `util/`, DB helpers, tests in `test/`
- `src/docker/` — container build and compose wrappers (`dc`, `dc.cpu`)
- `src/envs/` — documented env defaults (keep credential lines commented; real values go in uncommitted `src/docker/.env`)
- `src/bootstraps/` — CloudFormation templates published to the public S3 bucket and deployed by customers
- `.github/workflows/` — CI, CVE scan, and the S3 template / DockerHub publish workflows

## Validation

```bash
(cd src/python && ./bin/lint.sh && python3 -m pytest test)
```

## Skills

Reusable agent workflows live in `.agents/skills/`:

- `.agents/skills/plan/SKILL.md` — opt-in, file-based task plans with anti-drift rules for multi-session or multi-PR work
- `.agents/skills/review/SKILL.md` — multi-wave PR review (per-dimension, per-file findings + adversarial verification), including GitHub Actions supply-chain and CloudFormation template checks

Both write working files under `plans/`, which is gitignored.

If your tool expects skills elsewhere, symlink it, e.g. for Claude Code: `mkdir -p .claude && ln -s ../.agents/skills .claude/skills`
