# Packaging provenance and scope

[Home](../README.md) · [Evidence routes](EVIDENCE_ROUTES.md)

This candidate is built in a separate worktree on `github-repository-upgrade-v1`, based on the old public main commit. The original dirty scientific workspace is preserved. No training, model inference, checkpoint loading, manuscript edit or scientific-result recomputation was performed.

The [evidence manifest](../studies/mlbd2026_wrong_label_organization/manifests/evidence_manifest.json) binds every imported artifact to its original project-relative path, original SHA256, packaged SHA256, size and transformation. Scientific CSV values are copied byte-for-byte. The original project was dirty; its Git HEAD is context, not the complete scientific snapshot identity.

Three JSON files required replacement of machine-specific `/root/` locations with external-asset labels. Each modified field is listed in the manifest; original source hashes are retained. No numerical scientific field, seed or outcome is changed. These redacted files are inspection contracts, not runnable path configurations.

Historical implementation files are byte-identical snapshots. Their original directory dependencies are not relocated or silently fixed. They are explicitly inspection-only until a separately verified portable adapter exists. Missing data, model, order and support assets are described in [Reproducibility](REPRODUCIBILITY.md).

Private audit files, broad file inventories and local absolute paths live outside this public candidate. Caches, weights, datasets, temporary dumps, chat/session records, screenshots, private correspondence, manuscript projects and duplicate backups were not imported. Exclusion is not deletion from the research archive.

The old public tree contained planning documentation and placeholders, not current scientific code/results. Selected obsolete planning files were removed only from this new candidate, after byte comparison with the public base (allowing Git checkout line endings). All remain in that commit's history. No scientific asset was moved.

Presentation adopts concise reading routes, bounded results, separate evidence/provenance, explicit reproduction limitations and local diagrams from the [ECG reference repository's organization](https://github.com/PinkTulips139/PTBXL-ECG-FM-Benchmark-Reproduction). It does not reuse its study content, reviewer implementation, bundles or infrastructure.
