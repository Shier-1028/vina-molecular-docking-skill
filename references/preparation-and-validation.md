# Preparation and validation gates

## Identity before conversion

Join ligand records by verified CID plus structure, never by file order after
sorting a manifest. Detect duplicate IDs rather than silently overwriting a
dictionary entry. Record parent compound, state ID, name, source, CID, isomeric
SMILES/InChIKey, formal charge, unspecified stereocenters, and the actual 3D input.
Distinguish connectivity matches from full stereochemical matches. A specific
PubChem 3D conformer may be more stereospecific than its parent CID; it does not
establish the natural stereoisomer. A database hit does not establish botanical
occurrence. Keep synthetic controls separate from claimed plant constituents.

PubChem 3D is a starting geometry. A 2D record can be used after documented 3D
generation. RDKit AddHs is not a pH predictor. Select protonation and tautomer
rules, including ionizable groups and keto/enol alternatives when
relevant. Keep states linked to parents; do not count them as new compounds.
Reasonable original 3D may be retained; record whether optimized, the force field,
convergence, unsupported chemistry, and geometry checks. No silent force-field
fallback. Compare true heavy elements and graph identity after conversion;
nonpolar hydrogen merging means total atom counts need not match.

## Receptor identity, repair, and chemistry

Select target/species/domain, construct, mutations, chains/assembly, and pocket
evidence. Retain all chains needed for an interface pocket. Select exactly one
co-crystal ligand by residue name, chain, residue number, insertion code, and
consistent altloc. Do not mix A/B alternatives or different ligand copies.
After selecting a coherent altloc, clear retained altloc labels if the installed
preparer requires it; preserve the choice in the manifest.

Preserve the raw PDB/mmCIF sequence and missing-residue annotations. A cleaned
coordinate-only PDB may make PDBFixer report no missing residues because SEQRES
was stripped. That is not evidence of completeness. Distinguish missing entire
segments from missing atoms in present residues. Repair justified sidechains;
do not rebuild every absent loop/terminus automatically. Assess pocket impact.

Map repaired residues by chain, sequence alignment, insertion codes and residue
identity, including HETATM modifications. Count equality or sorted residue-number
zip alone is insufficient. Preserve a bijective mapping and investigate gaps.
Check original heavy coordinates using the retained altloc and documented
equivalent atom permutations (for example terminal O/OXT); separately report
renaming, newly built atoms and actual displacement.

Do not routinely remove whole incomplete residues to satisfy Meeko. Inspect
bond orders, element fields, altlocs, termini, disulfides, templates, and nonbonded
overlaps. Repair sidechains and constrain or fix the original atoms when local
optimization is needed. Record force field, restraint versus zero-mass fixing,
the exact fixed-atom set, iterations/tolerance, final force or termination reason,
energy change and original-atom displacement. Absolute energy alone does not
prove convergence; a minimum heavy-atom distance alone does not prove geometry.
Use topology to separate covalent bonds from nonbonded clashes.

If a remote region must be omitted, document scientific justification, every
removed residue, chain continuity/capping/terminal charges and a sensitivity
check where relevant. A distance of 5 or 8 A to existing atoms is not a universal
safe-deletion rule; missing sidechains may extend closer. Do not loosen thresholds
just to get a successful conversion. Keep failed models distinct from repaired
models. Avoid automatic `--delete_bad_res` without auditing exactly what it did.

Modified residues need connection, template, protonation and atom-type checks.
Presence of expected elements and successful conversion do not establish correct
chemistry. Partial charge values alone do not establish formal charge. Review
metals/cofactors and water retention according to the binding mechanism.

PDBFixer/OpenMM APIs are version-sensitive. Inspect installed signatures and
actual missingAtoms/nonstandardResidues structures rather than guessing their
shape. If OpenCL is broken, an available CPU platform is a valid recorded fallback;
it is not a requirement for every machine.

## Co-crystal and macrocycle preparation

Keep an unchanged experimental reference and a separate docking input. Restore
bonds from CCD or another authoritative chemical graph, preserving heavy-atom
coordinates and atom correspondence. Actually compare graph/stereochemical
identity; merely printing an InChIKey is not a check. Resolve altloc duplicates
before interpreting a template atom-count mismatch as covalent chemistry.
Confirm covalent links from LINK/struct_conn and chemistry. A free CCD ligand
may differ from a covalent adduct; standard noncovalent validation may not apply.

For Meeko macrocycles, `CGn` denotes a real carbon with a closure-related type;
`Gn` is a glue pseudoatom. Exclude Gn from chemical heavy-atom counts, geometric
contacts and crystal RMSD, but retain CGn as carbon and preserve all types in
Vina inputs. Record closure behavior and geometry. Descriptor rotatable-bond
counts, PDBQT TORSDOF and active branch counts are different measurements.

## Grid and global validation

Use the selected reference copy and actual pocket to locate the grid. Include
the co-crystal and the screening library in coverage checks, not just one group.
For center c and size s, inspect each real atom using abs(x_i-c_i) <= s_i/2 and
report boundary clearance. Consider flexible conformers and orientation space.
The Euclidean longest pair distance exceeding the shortest box edge does NOT
prove a particular pose cannot fit: its per-axis extents determine that.
Diameter plus padding is only a conservative orientation heuristic. A larger
box may reduce sampling efficiency; choose margins from the site and ligand.

Validate on the final receptor, box, state, scorer and parameters. Preserve each
seed result. Compute top-1 RMSD first and separately report whether lower-ranked
poses recover the crystal. Do not replace top-1 with the minimum-RMSD pose.
Use an explicit bijection of all real heavy atoms and symmetry mappings from
the correct graph (including stereochemistry), in the same receptor frame,
without fitting the ligand. Check mapping cardinality, element consistency,
reference-coordinate agreement and symmetry enumeration limits. Nearest-neighbor
mapping without uniqueness checks can produce falsely low RMSD. For different
receptor frames, align receptors first and apply that transform to ligands.

Vina RMSD bounds describe poses relative to the run's best pose. Neither those
bounds nor a docking score are crystal-validation RMSD. Record the predefined
acceptance rule; a common practical rule is top-1 <=2 A over three independent
seeds, plus pocket interactions and collision checks. Mixed seeds mean unstable.
Absent applicable co-crystal validation means unvalidated/exploratory, not passed.

For a failure, check mapping, states, receptor model, actual grid containment,
macrocycle closure and sampling before assigning a cause. Change one factor at a
time where feasible. Score-only/local-only can diagnose local compatibility but
cannot prove correct global ranking, a unique failure mechanism, or absence of
preparation error. Never delete a real pocket residue simply to improve RMSD.
Bound retries to a documented diagnostic plan; unresolved failures remain failed.
Any material input or scorer change invalidates the old validation status.
