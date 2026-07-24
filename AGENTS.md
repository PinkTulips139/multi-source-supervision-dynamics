# AGENTS.md

Instructions for future Codex sessions working in this repository.

## Required Context Before Editing

Before making substantive changes, read:

1. `README.md`
2. `docs/roadmap.md`
3. `docs/progress_log.md`

## Research Integrity Rules

- Do not fabricate experiments, numbers, paper results, citations, or performance claims.
- Clearly distinguish:
  - Literature-supported findings
  - Working hypotheses
  - Experimental results
- Do not describe planned work as completed work.
- Do not use phrases such as “proved,” “significantly improves,” or “outperforms all baselines” unless supported by actual repository results.

## Experiment Rules

New experiments must:

- Fix random seeds.
- Save configuration files.
- Record the environment.
- Output reproducible commands.
- Preserve raw outputs or enough metadata to regenerate them.
- Update `docs/progress_log.md` after substantive work.

## Safety and Privacy Rules

Do not commit:

- API keys
- `.env` files
- Private chat logs
- Paper PDFs
- Large datasets
- Model weights
- Personal privacy information
- Private notes

## Scope Rule

Do not modify files outside this repository working directory.

## Repository Hygiene

- Keep documentation honest and reproducible.
- Avoid empty directory sprawl.
- Do not create fake CSV results, fake plots, fake model outputs, or placeholder claims that look like results.
- When adding a result, include the command, config, date, and limitations.