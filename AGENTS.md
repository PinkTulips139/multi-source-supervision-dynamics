# Research repository governance

Read [README](README.md), the [study](studies/mlbd2026_wrong_label_organization/README.md), its [evidence manifest](studies/mlbd2026_wrong_label_organization/manifests/evidence_manifest.json), and [limitations](docs/KNOWN_LIMITATIONS.md) before editing result-facing files.

- Current explicit user instructions take precedence. Verified files determine state; notes and old conversation context are contextual only.
- Never fabricate experiments, numbers, citations or claims. Separate hypothesis, plan, observation and result. Manuscript claims must not exceed evidence.
- The current study is single-generation. Recursive propagation, collapse and mitigation claims require separate validated experiments. Do not claim lower correlation is always better, smoothness is irrelevant, or a unique mediator is identified.
- Preserve canonical results, manual manuscript text, frozen protocols, failed runs and negative evidence. No silent recomputation, overwrite, deletion or cosmetic improvement.
- Do not rerun expensive training, inference or GPU experiments without explicit authorization. Packaging is not training authorization.
- Preserve fixed seeds, configs, identities, environments, commands and provenance. Record deviations. Git HEAD identifies committed content only; dirty artifacts require source hashes.
- Do not execute historical reference builders as a shortcut. Their external dependency graphs are incomplete; read [reproduction limits](docs/REPRODUCIBILITY.md).
- No credentials, `.env`, private email, chat/session logs, submission correspondence, weights, raw datasets or machine-specific secrets in public files.
- Never use `git reset --hard`, `git clean -fd`, `git clean -fdx`, force push or automatic deletion of failed-run provenance. Audit before moving assets; use isolated worktrees when dirty.
- Stage explicit paths only, never `git add .` or `git add -A`. Publishing, rename, releases and settings changes require explicit task authorization.
- No automatic blanket licensing; respect third-party terms. Add author identities and citation metadata only after verification.
- Run the package verifier and `git diff --check` after changes. Changing expected hashes requires authoritative source review and a recorded reason.
- Add shared modules only when supported by real code and checked dependencies. Avoid empty scaffolding and duplicate scientific data.
