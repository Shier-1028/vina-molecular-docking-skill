---
name: vina-molecular-docking
description: Prepare, validate, run, resume, and audit AutoDock Vina molecular docking on Windows, including multi-receptor batches, co-crystal redocking, macrocycles, scoring comparisons, and traceable reports.
---

# AutoDock Vina 1.2.7 Molecular Docking

Use Vina's native batch interface or another equivalent auditable batch runner.
Scoring-function comparison is supported but optional; do not run extra scorers
unless the user requests or approves the comparison.
Local executables are `D:\autodockvina\vina.exe`, `D:\Anaconda\python.exe`, and
`D:\Anaconda\Scripts\mk_prepare_{receptor,ligand}.exe`. Verify paths before use;
these are configurable local locations, not portable installation requirements.

## Workflow

For a new project or a reusable handoff, start with
[project-template.md](references/project-template.md) and its configurable JSON
asset. It defines manifests, stage deliverables and failure branches for arbitrary
targets and libraries. Existing project layouts can be retained.

1. Verify Vina version and help. The optional `scripts/check_vina_env.ps1` checks
   Vina, Python, and Meeko; missing or unlaunchable required tools must fail.
   PyMOL is optional. Already prepared PDBQT inputs need no Meeko execution.
2. Record ligand identity/source/stereochemistry, receptor PDB/chain, pocket
   evidence, and observed versus expected chain residues. Review missing pocket
   residues, altlocs, cofactors, metals, and waters instead of deleting all HETATM.
3. Prepare validated PDBQT files after selecting pH and protonation states.
   Charge assignment is not protonation or hydrogen placement. Read the
   preparation section in [workflow.md](references/workflow.md) and
   [preparation-and-validation.md](references/preparation-and-validation.md)
   before preparing structures or evaluating a redocking failure.
4. Classify each receptor as `formal`, `exploratory`, `N/A`, or `void`. Use a shared numeric box/search config with no `receptor`, `ligand`, `maps`,
   `scoring`, `out`, or `dir` entries. Group batches by receptor and box.
   Vina box sizes are lengths in Angstrom, not AutoGrid point counts.
   For a `formal` receptor with an applicable co-crystal small molecule, perform
   the predeclared global co-crystal redocking validation. A receptor without an
   applicable co-crystal ligand is `N/A` for co-crystal redocking, not a failed
   validation; it may still support explicitly labeled exploratory docking when a
   site is supported by literature or documented pocket analysis. Record top-1
   symmetry-corrected heavy-atom RMSD in the receptor frame, without ligand
   fitting. A common predeclared criterion is <=2 A across three seeds, but the
   threshold, seed count, and top-1/best-mode rule are project choices. A failed
   validation blocks the validation claim, not explicitly requested exploratory
   docking.
5. Run `--receptor ... --config conf.txt --batch ligands --dir results/vina
   --scoring vina`. Vina 1.2.7 accepts a directory of lowercase `.pdbqt` files.
   Each scoring run loads the receptor/maps once and processes ligands in batch.
   Use a fresh output directory for every run; pre-create it before invocation.
6. Offer the user an optional scoring-function comparison. If requested, repeat
   with `vinardo`. For `ad4`, use `--maps prefix`
   in place of `--receptor`. AD4 requires AutoGrid4 maps from the same prepared
   receptor and matched box, covering all ligand atom types. Read the AD4 branch
   in [workflow.md](references/workflow.md) before running it. Missing maps mean
   AD4 is unavailable, not that vina or vinardo failed. Keep each scorer's run,
   ranking, and interpretation separate.
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

## Protection and provenance

- Grid generation, figure generation, and batch execution are read-only with
  respect to prepared receptor PDBQT files. They must not silently rerun receptor
  preparation or overwrite a validated receptor.
- Register and verify receptor SHA256 before batch execution. A mismatch aborts
  the run before any output is modified.
- Keep `formal`, `exploratory`, `N/A`, and `void` outputs separate in summaries,
  plots, and conclusions. A void result is retained for provenance but excluded
  from formal rankings.

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
- To reproduce an original docking score with `--score_only`, pass the original
  run's recorded `REMARK UNBOUND` value as `--unbound_energy`. Default
  `score_only` may recalculate the unbound reference and must not be mixed with
  original scores without documenting the difference.
- Read [case-lessons.md](references/case-lessons.md) when applying lessons from
  the supplied DSH session. Its historical commands are examples to assess,
  not authorization to launch, stop, delete, or overwrite current jobs.

