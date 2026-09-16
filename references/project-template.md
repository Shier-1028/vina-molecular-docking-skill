# Reusable project template

Use for any target/library. Adopt existing project conventions when present.
The optional assets/project-template.json is a planning manifest, not a launchable
universal receptor preparer. Copy into a fresh project and resolve all nulls and
scientific choices before generating numeric Vina configs. Do not overwrite an
existing project manifest. Tool paths, number of receptors/ligands, CPU budget,
seeds, scores and thresholds are configurable; supplied numbers are examples.

## Directory convention

```text
project/
  raw/                     immutable source structures and ligand records
  manifests/               identities, state choices, preparation and project JSON
  prepared/                receptor and ligand PDBQT plus chemically typed SDF
  reference/               crystal reference, docking input and atom bijection
  runs/<run-id>/<target>/   config/input snapshots, validation, scorer outputs, logs
  reports/                 validated and exploratory matrices, figures and methods
```

## Minimum manifests

Ligand CSV columns:
`parent_id,state_id,name,source_id,source_url,isomeric_smiles,inchikey,formal_charge,
stereochemistry_basis,protonation_basis,tautomer_basis,geometry_method,input_sdf,
prepared_pdbqt,sha256,eligibility,exclusion_reason`.
Use one row per state, stable unique state IDs and one parent identity per compound.

Receptor preparation JSON should record raw source/hash, species/sequence/domain,
chains and assembly, mutations, insertion codes, altloc selection, missing segments,
rebuilt/deleted residues and justifications, cofactors/metals/waters, pH and residue
states, templates/charges, repair tools/versions, minimization evidence, original
atom mapping and displacement, model ID and final hash.

Run JSON should record ID, target model/state, input hashes and frozen config,
scorer, ligand state list/order, seed/CPU, command, timestamps, process identity,
exit status, log paths, validation identity and task-level completion/failure.
Reference RMSD atom-map JSON is a list of pairs `[reference_zero_based_index,
input_pdbqt_serial]` for every real heavy atom. Build it from preparation provenance
or a verified one-to-one element/coordinate match, not guessed atom order.

## Stage deliverables and gates

| Stage | Evidence to retain | Advance condition |
|---|---|---|
| Scope | target/library/controls, site question, requested scorers, resource budget | identities and objective explicit |
| Preparation | original and prepared structures, chemical states, atom mapping, preparation records | chemistry, geometry, pocket and coordinate checks resolved |
| Grid | exact numeric config and actual per-axis reference/library coverage | selected site and reasonable margins supported |
| Validation | per-seed complete output, top-1 RMSD, mapping, interaction/geometry review | predeclared rule met for this model/scorer/config |
| Batch | immutable run manifest, logs, all expected state outputs | exit/file/atom/provenance checks agree |
| Interpretation | within-target/scorer ranks, control comparisons, uncertainty, figures | only current validated data in primary conclusions |

Failure branches are explicit: repair and revalidate; choose a scientifically
justified alternate structure of the same target; or retain as not-run/exploratory.
Changing the target protein changes the scientific question and needs its own
selection rationale. Apo models, covalent sites, metals and flexible receptors
may need specialized validation rather than a routine noncovalent pass label.

## RMSD helper

`scripts/validate_redocking.py` uses RDKit and the included strict PDBQT parser.
Supply a chemically correct heavy-atom SDF with original crystal coordinates and
the explicit reference-index/input-serial bijection. It checks the input frame
against that reference, removes glue pseudoatoms by type, maps all true heavy
atoms and computes graph-symmetry RMSD without fitting. All requested outputs
must exist; list them explicitly rather than globbing only completed files.

```powershell
& $python "$skill/scripts/validate_redocking.py" --reference-sdf reference/crystal.sdf --input-pdbqt reference/input.pdbqt --atom-map reference/atom-map.json --outputs runs/run-001/target/validation/seed1.pdbqt runs/run-001/target/validation/seed42.pdbqt runs/run-001/target/validation/seed777.pdbqt --report runs/run-001/target/validation/rmsd.json --threshold 2 --required-pass-fraction 1
if ($LASTEXITCODE -ne 0) { throw 'Redocking incomplete, unstable or failed; inspect report' }
```

The helper validates poses, not run hashes, chemical preparation, reference source,
seed independence or interactions. Review those separately before granting
production_eligible. It reports top-1 and best recovered pose separately.
It intentionally rejects input coordinates differing from the crystal reference;
use a separately verified chemical mapping workflow if input geometry was changed.

## Reporting and reuse

Use report-template.md for the final methods and results. Preserve a concise
handoff with run IDs, validated status, pending tasks, active processes, paths and
restart conditions. The skill supplies preparation decisions and validation tools;
it does not claim fully automatic protein repair is chemically reliable.
