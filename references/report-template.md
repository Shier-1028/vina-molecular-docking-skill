# <TARGET> AutoDock Vina docking report

## 1. Objective
Target, adverse effect or phenotype (if applicable), candidate ligands, and the docking question.

## 2. Materials and software
Receptor PDB ID/chain, ligand sources, actual Vina version/path, Meeko version,
Python, optional preparation/visualization tools. Record actual resolved paths,
environment-check results and any version adaptations.
For AD4 scoring, include AutoGrid4 version and map generation provenance, or
explicitly state AD4 was not run and why.

## 3. Methods
- Receptor cleaning, completeness, retained cofactors/waters, pH, hydrogen
  preparation, residue protonation/template choices and charge model.
- Ligand 3-D generation, protonation/stereochemistry review, and PDBQT preparation.
- Vina config: center, box size, exhaustiveness, number of modes, energy range, seed if used.
- Native `--batch` commands, input list/order, per-function output directories,
  logs and config/input hashes. State expected/completed/failed counts.
- AD4 map prefix, covered ligand atom types, GPF/GLG, map origin/center, spacing
  and dimensions; document agreement of actual physical boxes after rounding.
- Contact and visualization criteria (4 Å pocket; 3.5–3.6 Å polar distances).
- Model/run IDs and input hashes; original/rebuilt/deleted residues and mapped
  atoms, restrained/fixed subset, convergence evidence, altloc selection and
  protonation/tautomer/stereochemistry state manifest.
- Global reference redocking per receptor and scorer on the final inputs:
  all seeds, top-1 score, graph-mapped unfitted symmetry-corrected heavy-atom RMSD,
  true heavy-atom count, predeclared threshold, pass fraction and final status.
  Report lower-rank recovery and local-only diagnostics separately.

## 4. Results
| Scoring | Rank within scoring | Ligand | Score (kcal/mol) | RMSD LB | RMSD UB | Modes | Status |
|---|---:|---|---:|---:|---:|---:|---|

Include a separate side-by-side table from `scoring_comparison.csv`. Leave
failed or not-run scores empty. RMSD bounds here are relative to each run's top
pose, not a cross-scoring or experimental-pose comparison.

Include paths to best poses, logs, configs, contact tables, and images.
Separate validated production, exploratory, failed, superseded and not-run data.
State the actual number of unique receptor/ligand-state/scorer jobs in each group.
Do not count interrupted or superseded files as current completed tasks.

## 5. Interpretation
Discuss rank agreement, pocket residues, atom-matched pose agreement and chemical
differences. Report seed sensitivity and reference-ligand redocking when tested.
Do not pool/average raw energies across scoring functions or call score agreement
independent experimental validation. Distinguish redocking under each scoring
function from fixed-pose rescoring with `--score_only`.
Do not infer cross-receptor selectivity or target-specific positive controls from
raw scores or an inhibitor's activity against another protein. Distinguish observed
diagnostic results from hypotheses about why validation failed.

## 6. Limitations
Rigid receptor, simplified solvent/entropy treatment, protonation and tautomer uncertainty, dependence on box placement and exhaustiveness, ligand-size bias, and distance-based contacts not being definitive hydrogen bonds.
