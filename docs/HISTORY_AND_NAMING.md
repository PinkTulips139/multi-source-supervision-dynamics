# History and naming strategy

[Home](../README.md)

## Histories actually found

The existing public repository's main tip was `bf78c9fe05eed084ae4abb672c08fe92f2819fc4` (2026-07-24); its root is `df3750cd4ef53e9f235711d1651d4c5624e02dfd`. The local research branch was `correlation-aware-phase0`, HEAD `365f48859e7e1f370dd13d40ea262eb0439d72de`, rooted at `b87765e4a350fb3e14a44ccc76f2fb9fd6c429e5`, with uncommitted research material and no configured remote.

After importing the local branch into a separate audit clone, `git merge-base` found no common ancestor. Consequently this packaging worktree starts from the **existing public main history** and imports explicitly selected scientific files by content hash. It does not pretend the two histories are a linear continuation, merge unrelated histories, rewrite commits or rebuild the original research workspace.

## Legacy assessment

| Legacy material | Current treatment |
| --- | --- |
| Reproducibility, fixed seeds, honest hypothesis/result separation | Retained and strengthened in governance |
| Motivation about multi-source dependence and long-term propagation | Retained as umbrella questions with future-work labels |
| Correlation-aware weighting and lower-correlation hypotheses | Historical hypotheses, not current validated claims |
| Gaussian simulation, IMDb/SST-2/AG News plans | Superseded as descriptions of the current CLINC150/BANKING77 study |
| “Formal experiments not completed” | Removed from current homepage; retained in historical snapshot |
| Preliminary objective and unverified reference list | Historical only; not a current algorithm or verified bibliography |
| Placeholder experiment/notebook/result directories | Removed from the candidate tree; original bytes remain in Git history |

The [original early-planning snapshot](https://github.com/PinkTulips139/multi-source-supervision-dynamics/tree/bf78c9fe05eed084ae4abb672c08fe92f2819fc4) remains addressable. The original [progress log](progress_log.md) remains as dated history with a current explanatory note.

The archival tag [`v0-early-planning-2026-07`](https://github.com/PinkTulips139/multi-source-supervision-dynamics/tree/v0-early-planning-2026-07) points to `bf78c9fe05eed084ae4abb672c08fe92f2819fc4`. It identifies the actual public July state, not the unrelated local branch.

## Repository name

The repository name **`multi-source-supervision-dynamics`** fits current wrong-label organization and Student consequence studies while leaving room for recursive dynamics and possible mitigation. The old name foregrounded a correlation-aware method and recursive validation that are not current demonstrated contributions. The new name offers a stable umbrella without committing future findings to one mechanism or hypothesis.

GitHub documents redirects for repository traffic and old clone/fetch/push URLs after a rename, but recommends updating local remotes; project site URLs are an exception. Reusing the old name can break redirects. See [GitHub's rename guidance](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository).

Commit-based evidence links and the archival tag identify the historical state independently of the repository name. This repository upgrade is a main-branch commit; no GitHub Release is implied by the archival tag.
