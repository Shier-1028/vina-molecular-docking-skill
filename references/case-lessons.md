# General troubleshooting and interpretation

Use these checks when preparing inputs, diagnosing failed validation, or reviewing
batch results. Parameters and acceptance criteria belong to the current project.

| Potential problem | Recommended check |
|---|---|
| Ligand labels assigned by file order | Join by verified chemical identity; reject duplicate identifiers and mismatches |
| Text decoding fails | Specify producer/reader encodings and retain raw logs |
| Original atoms appear displaced | Compare selected altlocs and chemically justified equivalent atom names |
| Incomplete residues fail preparation | Repair geometry and templates; justify any omission rather than relaxing thresholds to force conversion |
| An obsolete receptor is selected | Resolve inputs from a versioned manifest, not filename precedence |
| Batch starts after failed redocking | Gate production on validation status, not script exit code alone |
| Macrocycle pseudoatoms distort analysis | Exclude glue pseudoatoms from chemical counts and RMSD; retain real closure carbons |
| A ligand is assumed to exceed its box | Check per-axis containment and clearance; diameter alone cannot prove clipping |
| Minimization is declared converged from energy alone | Inspect termination, force criteria, fixed-atom mapping and displacements |
| Crystal and predicted poses have different scores | Assess preparation, states, geometry and sampling before assigning a failure mechanism |
| Local optimization is mistaken for global validation | Report local compatibility separately from global pose recovery |
| Completion totals include excluded or obsolete tasks | Count current completed pairs separately from failed, excluded and diagnostic runs |
| Scores are used to claim cross-target selectivity | Require target-specific evidence and appropriate controls |
| A running process is declared completed | Verify exit state and complete expected outputs |

Recompute chemical descriptors for the selected structure and state. Descriptor
rotatable-bond counts, PDBQT TORSDOF and active branch counts are not interchangeable.
Do not infer a preference for extended poses solely from a torsion penalty;
comparisons also depend on intermolecular and internal energy terms.

Ordinary noncovalent docking does not model covalent bond formation. An atom-count
mismatch alone cannot diagnose adduct chemistry: resolve altloc duplicates, inspect
LINK/struct_conn records, and verify the selected chemical graph.

Progress bars and CPU activity are operational indicators, not completion or
scientific-validity criteria. Follow execution-and-provenance.md for run tracking.
