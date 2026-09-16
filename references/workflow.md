# Native Vina 1.2.7 workflow on Windows

Before production, apply [preparation-and-validation.md](preparation-and-validation.md).
For multi-receptor runs and recovery use [execution-and-provenance.md](execution-and-provenance.md).
The CLI examples below assume applicable validation has passed or the user has
scoped an explicitly exploratory run. Run only the requested scoring functions.

## Paths and preparation

The commands below use PowerShell as the terminal, not a docking wrapper script.
Set the working directory to the docking project. Resolve actual executable paths:

```powershell
$tools = (Get-Content -LiteralPath ./local-tools-prepared.json -Raw | ConvertFrom-Json).tools
$vina = $tools.vina
$python = $tools.python
$prepareRec = $tools.prepare_receptor
$prepareLig = $tools.prepare_ligand
& $vina --version
& $vina --help
& $prepareRec --help
& $prepareLig --help
```

Record software versions and exact commands. For a full preparation environment,
the skill's optional `scripts/check_vina_env.ps1` fails on missing required tools.
Do not use `python check_vina_env.ps1`: it is a PowerShell script.

Select pH from assay conditions (record an explicit assumption when unknown).
Repair justified missing atoms and add hydrogens with an available preparation
tool, such as PDB2PQR/Reduce, recording the tool/version/settings. Inspect His
tautomers (HID/HIE/HIP), Asp/Glu, Lys/Cys, termini, and metal-coordinating residues
in the pocket; inspect ligand tautomers/stereochemistry too. Protonation variants
are separate inputs. `--compute_charges` assigns partial charges; it does not
choose pH, determine all protonation states, or replace hydrogen preparation.

Keep an explicit residue-state record. Verify Meeko's templates preserve the
intended states; installed Meeko supports `--set_template` (for example
`A:17=HID`, only when that residue/state is actually intended). Avoid silently
deleting residues that do not match templates. Inspect prepared hydrogen placement.
Retain essential cofactors/metals and justified waters; choose an appropriate
parameterization if ordinary scoring is inadequate.

Example for already reviewed structures (local Meeko options verified with help):

```powershell
& $prepareRec --read_pdb receptor_protonated.pdb -o receptor -p --compute_charges --charge_model gasteiger
& $prepareLig -i ligand_protonated.sdf -o ligands\ligand.pdbqt
```

Create directories first. Vina only reads prepared PDBQT ligands, not SDF/MOL2.
Standard vina/vinardo scores do not use AD4's explicit electrostatic term;
protonation still affects donor/acceptor atom typing. AD4 maps and scoring also
depend on partial charges. Gasteiger is a conventional AD4 choice; justify other
models rather than silently changing charges between comparisons.

## Shared config

Use `conf.txt` for numeric box/search settings only. The following coordinates
are illustrative, not a universal pocket. Replace them from site evidence.

```ini
center_x = 10.0
center_y = 20.0
center_z = 30.0
size_x = 20.25
size_y = 20.25
size_z = 20.25
exhaustiveness = 16
num_modes = 20
energy_range = 3
seed = 42
cpu = 4
```

Keep `receptor`, `ligand`, `batch`, `maps`, `scoring`, `out`, and `dir` out of
this shared file; supply them per invocation. Sizes are Angstrom lengths.
Use one batch per receptor/box/protonation preparation. Archive config and inputs
(or their hashes), ligand list/order, version, seed and command. For repeatable
ordering pass an explicit sorted array after `--batch`; native directory traversal
does not promise sorted order. Different scoring functions can find different
poses even with the same seed. Test additional seeds when assessing stability.

## Native batch docking

Each invocation loads a receptor/maps once for the batch, not once per ligand.
Keep only intended inputs in a flat `ligands` directory, with unique stems and
lowercase `.pdbqt` extensions. Directory mode is nonrecursive. The output directory
must already exist; use a fresh run root to prevent old poses masking skipped jobs.

```powershell
New-Item -ItemType Directory -Path results\run01\vina,results\run01\vinardo | Out-Null
& $vina --receptor receptor.pdbqt --config conf.txt --batch ligands --dir results\run01\vina --scoring vina > results\run01\vina.log 2>&1
if ($LASTEXITCODE -ne 0) { throw 'Vina batch failed; inspect vina.log' }
& $vina --receptor receptor.pdbqt --config conf.txt --batch ligands --dir results\run01\vinardo --scoring vinardo > results\run01\vinardo.log 2>&1
if ($LASTEXITCODE -ne 0) { throw 'Vinardo batch failed; inspect vinardo.log' }
```

No per-ligand loop or `--out` is needed for batch mode. Native output names are
`results/run01/<scoring>/<ligand>_out.pdbqt`. They contain multiple poses, not just
the best one. Do not pass `--ligand` together with `--batch`; multiple `--ligand`
inputs mean simultaneous docking, not independent batch docking. Do not use the
removed `--log` option; redirect the terminal output as shown.

For selected inputs and stable order instead of a whole directory:

```powershell
$ligands = @(Get-ChildItem -LiteralPath ligands -File | Where-Object { $_.Extension -ceq '.pdbqt' } | Sort-Object Name | ForEach-Object FullName)
if ($ligands.Count -eq 0) { throw 'No PDBQT ligands' }
New-Item -ItemType Directory -Path results\run02\vina | Out-Null
& $vina --receptor receptor.pdbqt --config conf.txt --batch $ligands --dir results\run02\vina --scoring vina
if ($LASTEXITCODE -ne 0) { throw 'Vina batch failed' }
```

## AD4 scoring branch

`--scoring ad4` is supported in Vina, but requires AutoGrid4 affinity maps.
It rejects `--receptor`; substituting only `--scoring` in a config containing
`receptor` is invalid. Supply `--maps` with a prefix, not a `.maps.fld` filename.

Generate maps once from the exact prepared receptor. Meeko `-g` can generate a
GPF alongside PDBQT with `--box_center X Y Z --box_size X Y Z`; use the same
preparation/state settings as the other scoring runs. Inspect the GPF's ligand
types and extend them to cover every atom type in the entire ligand library.
For a new preparation matching the illustrative shared box, run from a separate
maps preparation directory (do not overwrite a previously reviewed receptor):

```powershell
& $prepareRec --read_pdb receptor_protonated.pdb -o receptor -p -g --compute_charges --charge_model gasteiger --box_center 10 20 30 --box_size 20.25 20.25 20.25
```

Preserve any residue-template overrides in this command. Compare the produced
receptor PDBQT to the reviewed docking receptor before using the maps.
Run the installed AutoGrid4 executable by its actual D-drive path, for example
(the path below is illustrative, not an installed-tool claim):

```powershell
# Run from the maps directory so GPF relative receptor/map paths resolve.
& $autogrid -p receptor.gpf -l receptor.glg # set $autogrid to the selected executable
if ($LASTEXITCODE -ne 0) { throw 'AutoGrid failed' }
```

Before Vina, check AutoGrid completion and required `receptor.maps.fld`, atom-type
`receptor.<type>.map`, electrostatic `receptor.e.map`, and desolvation
`receptor.d.map` files. Maps must share dimensions/origin/spacing and receptor
preparation; preserve GPF/GLG and hashes. Map header `CENTER`, `NELEMENTS`, and
`SPACING` define the AD4 search box. Its physical size is `NELEMENTS * SPACING`;
match Vina's center and sizes to that actual box after grid rounding. Supplying
different box values in `conf.txt` does not resize loaded AD4 maps. Do not substitute
Vina-generated maps for AutoGrid AD4 maps.

From the project directory, with maps under `maps/receptor.*`:

```powershell
New-Item -ItemType Directory -Path results\run01\ad4 | Out-Null
& $vina --maps maps\receptor --config conf.txt --batch ligands --dir results\run01\ad4 --scoring ad4 > results\run01\ad4.log 2>&1
if ($LASTEXITCODE -ne 0) { throw 'AD4 batch failed; inspect ad4.log' }
```

If AutoGrid/maps are unavailable, complete vina/vinardo and report AD4 as not run.
This branch needs no AutoDock4 docking executable, DPF, DLG, or legacy scripts.

## Single-ligand scoring comparison

Use the same prepared ligand and shared config; `run01` must already exist:

```powershell
& $vina --config conf.txt --receptor receptor.pdbqt --ligand ligands\ligand.pdbqt --scoring vina --out results\run01\run_vina.pdbqt
& $vina --config conf.txt --maps maps\receptor --ligand ligands\ligand.pdbqt --scoring ad4 --out results\run01\run_ad4.pdbqt
& $vina --config conf.txt --receptor receptor.pdbqt --ligand ligands\ligand.pdbqt --scoring vinardo --out results\run01\run_vinardo.pdbqt
```

These commands redock. For true fixed-pose rescoring, pass a single extracted
pose as `--ligand` with `--score_only` and save stdout separately. Do not treat
score-only output as a new docked PDBQT or feed it to the batch summarizer.

## Summaries and contacts

The summarizer uses each output PDBQT's `REMARK VINA RESULT` records, which Vina
1.2.7 writes for all three scoring functions. Scoring identity comes from the
explicit directory/run provenance, not from the word VINA in the remark.

```powershell
# Set $skill to the actual installed/extracted skill directory.
& $python "$skill\scripts\summarize_vina_results.py" --ligand-dir ligands --results-dir results\run01 --scoring vina vinardo ad4
if ($LASTEXITCODE -ne 0) { throw 'Incomplete results; inspect docking_summary_all.csv' }
& $python "$skill\scripts\summarize_geometric_contacts.py" --summary results\run01\docking_summary_all.csv --receptor receptor.pdbqt --out-dir results\run01\contacts
```

Use `--scoring vina vinardo` when AD4 was not requested/run. Each expected ligand
gets a row per requested scoring function; missing/truncated/unscored files are
errors, not zero scores. The summarizer extracts one pose per successful pair
under `best_poses/<scoring>` and creates:

- `docking_summary_all.csv`: status, per-function rank, score, RMSD bounds, count,
  input/output/best-pose paths, and error details.
- `scoring_comparison.csv`: one ligand per row, scores and ranks side by side.

RMSD bounds are relative to each run's top pose. For cross-function or crystal
pose RMSD, use consistent atom mapping, symmetry treatment, and receptor frame.
Compare within-function ranks, pose agreement and contact consistency; do not
pool or average raw vina/vinardo/AD4 energies into one global ranking. Redocking
the reference ligand and checking known interactions provides additional validation.

Optional PyMOL views: pocket with ligand/pocket residues and selective labels;
overview without labels. Use extracted single poses, inspect image clarity, and
describe 4-Angstrom pocket neighbors / 3.6-Angstrom polar distances as geometric
contacts. They do not establish hydrogen bonds without donor/acceptor geometry.

## Verified references

- [Vina 1.2.7 CLI source](https://github.com/ccsb-scripps/AutoDock-Vina/blob/v1.2.7/src/main/main.cpp)
- [Batch docking](https://autodock-vina.readthedocs.io/en/latest/docking_in_batch.html)
- [Basic docking and AD4 maps](https://autodock-vina.readthedocs.io/en/latest/docking_basic.html)

The baseline Vina 1.2.7 help was checked against the versioned source during
development. Verify the recipient's installed version rather than assuming the
developer's executable or command interface is present.
