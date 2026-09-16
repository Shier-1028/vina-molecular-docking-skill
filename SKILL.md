---
name: vina-molecular-docking
description: Prepare, validate, run, resume, and audit AutoDock Vina molecular docking on Windows, including multi-receptor batches, co-crystal redocking, macrocycles, scoring comparisons, and traceable reports.
---

# AutoDock Vina Molecular Docking

Use native Vina commands for docking, not a per-ligand PowerShell launcher.
Before first use on a new machine, read [first-use.md](references/first-use.md).
Explain task-specific dependencies, ask for software paths or permission to scan
selected installation folders, and perform capability checks in the chosen Python
environment. A skill installation has no guaranteed automatic setup hook: show
the reminder when first invoked. Never assume a drive, installation directory or
that software is bundled. Preserve established local configuration on later runs.
For deployment limits and troubleshooting handoff, read
[distribution-review.md](references/distribution-review.md).

## Workflow

For a new project or a reusable handoff, start with
[project-template.md](references/project-template.md) and its configurable JSON
asset. It defines manifests, stage deliverables and failure branches for arbitrary
targets and libraries. Existing project layouts can be retained.

1. Verify Vina version and help using `scripts/check_environment.py` or its
   PowerShell wrapper; choose dock/prepare/validate/repair profiles as needed.
   Check capabilities, not an exact version alone; missing required features fail.
   PyMOL is optional. Already prepared PDBQT inputs need no Meeko execution.
2. Record ligand identity/source/stereochemistry, receptor PDB/chain, pocket
   evidence, and observed versus expected chain residues. Review missing pocket
   residues, altlocs, cofactors, metals, and waters instead of deleting all HETATM.
3. Prepare validated PDBQT files after selecting pH and protonation states.
   Charge assignment is not protonation or hydrogen placement. Read the
   preparation section in [workflow.md](references/workflow.md) and
   [preparation-and-validation.md](references/preparation-and-validation.md)
   before preparing structures or evaluating a redocking failure.
4. Use a shared numeric box/search config with no `receptor`, `ligand`, `maps`,
   `scoring`, `out`, or `dir` entries. Group batches by receptor and box.
   Vina box sizes are lengths in Angstrom, not AutoGrid point counts.
   Before production batching, validate each receptor/scorer/preparation/final-box
   combination by applicable global co-crystal redocking. Record top-1 symmetry-
   corrected heavy-atom RMSD in the receptor frame, without ligand fitting.
   A common predeclared criterion is <=2 A across three seeds; report mixed
   outcomes as unstable, not universally passed. This is a reference criterion,
   not proof of biological activity. If validation fails, block validated
   production; explicitly scoped exploratory work stays separately labeled.
5. Run `--receptor ... --config conf.txt --batch <sorted ligand paths> --dir results/vina
   --scoring vina`. Vina 1.2.7 accepts a directory of lowercase `.pdbqt` files.
   Each scoring run loads the receptor/maps once and processes ligands in batch.
   Prefer explicit sorted files across versions; verify directory mode before use.
   Use a fresh output directory for every run; pre-create it before invocation.
6. For scoring comparison, repeat with `vinardo`. For `ad4`, use `--maps prefix`
   in place of `--receptor`. AD4 requires AutoGrid4 maps from the same prepared
   receptor and matched box, covering all ligand atom types. Read the AD4 branch
   in [workflow.md](references/workflow.md) before running it. Missing maps mean
   AD4 is not run, not that vina/vinardo failed.
7. Save stdout/stderr by shell redirection (1.2.7 has no `--log`). Check exit codes
   AND expected ligand outputs: Vina may skip malformed ligands with exit code 0.
   Preserve original multi-model `<ligand>_out.pdbqt` files.
   For long jobs, resuming, or multiple receptors, read
   [execution-and-provenance.md](references/execution-and-provenance.md).
   A process, a progress bar, a file, and an exit code are distinct evidence;
   none alone establishes successful, validated completion.
8. Run `scripts/summarize_vina_results.py` with the input ligand directory,
   results directory, and explicitly requested scoring functions. It checks each
   expected output, extracts a single best pose, ranks within each scoring function,
   and writes long and side-by-side CSV tables. Failures remain visible and cause
   nonzero exit. See workflow for commands and the new interface (no jobs CSV).
9. Optionally run `scripts/summarize_geometric_contacts.py` on successful summary
   rows. Make pocket and overview images; use single extracted poses, never all
   modes merged together. Label geometric polar distances as potential contacts,
   not proven hydrogen bonds. Use [report-template.md](references/report-template.md).

## Interpretation

- `vina`, `vinardo`, and `ad4` runs are separate docking searches; compare rank
  stability, matched-atom poses and key interactions. Do not globally rank or
  average their raw scores, or call agreement independent experimental validation.
- RMSD lower/upper bounds in Vina output are relative to that run's best pose,
  not to a crystal pose or another scoring run.
- Fixed-pose rescoring is a separate `--score_only` workflow on a single pose;
  it is not equivalent to changing `--scoring` and redocking.
- Vina/vinardo need no AutoGrid. AD4 uses GPF/GLG/maps only for map generation;
  docking still uses Vina 1.2.7, with no AutoDock4 executable, DPF, or DLG.
- Do not infer cross-target selectivity from raw docking scores or call a known
  inhibitor of a different protein a validated positive control. Confirm target-
  specific evidence and compound provenance, especially in natural-product lists.
- `--local_only` near a crystal pose and `--score_only` are diagnostic evidence,
  not substitutes for successful global redocking. A worse crystal score does
  not isolate scoring bias from receptor/state/preparation/sampling errors.
- Read [case-lessons.md](references/case-lessons.md) for general troubleshooting
  checks and common interpretation errors.

