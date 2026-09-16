# First use, dependencies and portability

A skill ZIP is instructions and helpers, not an executable installer. Standard
skill loading has no guaranteed post-install hook. Show this onboarding checklist
on the FIRST INVOCATION (or immediately when the host installation conversation
allows it). Never claim that merely unzipping the skill installs software or runs
checks. No software, commercial licenses or model files are bundled.

## Tell the user what is needed

| Requested work | Dependencies |
|---|---|
| Dock prepared PDBQT | Official AutoDock Vina CLI; Python >=3.9 for result checks |
| Prepare ligands/receptors | RDKit, Meeko and its CLI in the selected Python environment |
| Crystal RMSD validation | RDKit with 3D, InChI and CalcRMS functionality |
| PDBFixer repair workflow | PDBFixer, OpenMM and an available working platform |
| Images | PyMOL or another chosen viewer; optional for docking |
| AD4 scoring | AutoGrid4 plus valid matching receptor maps; optional, separately configured |

Ask for the desired work and either executable paths or permission to scan named
installation folders. First inspect explicit paths, saved project configuration
and PATH. Do not automatically recurse all disks. When multiple Python/Meeko
installations exist, present candidates and choose one coherent environment with
the user. Do not execute arbitrary discovered files before resolving the choice.
Check the actual machine OS: Windows native CLI is this package's tested scope.
For Linux/macOS use native binaries and Python checker with adapted shell commands;
those platforms are untested here. Do not mix WSL paths/binaries with Windows
processes. A GPU, CUDA, MGLTools, Open Babel or Anaconda is not universally required.

## Find and save paths

Set `$skill` to the actual extracted skill directory (not a historical D: path).
PATH-only discovery launches no candidate programs:

```powershell
& "$skill/scripts/find_tools.ps1"
# Only after the user chooses/authorizes standard installation roots:
& "$skill/scripts/find_tools.ps1" -Roots $env:ProgramFiles,$env:LOCALAPPDATA -MaxDepth 3 -MaxDirectories 2000
```

The scan skips reparse points, limits recursion, and reports truncation/unreadable
directories. A negative scan is not proof software is absent. Search an additional
user-selected folder or request its exact path. File names alone do not validate
the software. Paths with spaces must be passed as single quoted arguments.

Run with the selected Python executable. Use a fresh report name on each check:

```powershell
$python = (Get-Command python).Source # or use the selected environment's python executable
$vina = (Get-Command vina).Source
& $python "$skill/scripts/check_environment.py" --profile dock --vina $vina --report environment-dock.json --save-config local-tools.json
& $python "$skill/scripts/check_environment.py" --profile prepare --config local-tools.json --report environment-prepare.json --save-config local-tools-prepared.json
& $python "$skill/scripts/check_environment.py" --profile validate --report environment-validate.json
& $python "$skill/scripts/check_environment.py" --profile repair --report environment-repair.json
```

Run only profiles needed for the task. Preparation and repair profiles do not
recheck Vina; a complete workflow must also pass dock and validate. CLI overrides
are `--prepare-receptor` and `--prepare-ligand`. Meeko .py entry points use the
selected Python. The PowerShell wrapper exposes equivalent named parameters.
No registry/PATH changes or software installation occur. Saved config is local
to the user's project; never include their real paths in a redistributed ZIP.
If a saved Python differs, rerun under it or create a new configuration; do not
silently switch environments. Existing report/config files are not overwritten.

## Compatibility decision

Vina 1.2.7 is the tested CLI baseline, not the only allowed release. Probe actual
--version and --help for batch/dir/receptor/ligand/config/scoring/seed/cpu and maps
when requested. Other versions with those features receive a warning and need a
small actual-input smoke run plus redocking. Missing capabilities block native
batch use; suggest the official baseline or an explicitly reviewed adaptation.
Use explicit sorted file lists for batch portability; directory-mode behavior is
documented for 1.2.7 and must not be assumed for every release.

The checker imports packages in the exact selected interpreter, records versions,
tests RDKit 3D/InChI/RMSD, Meeko conversion of a tiny ligand, CLI flags, and an
OpenMM CPU context when repair is requested. These are capability tests, not a
certified compatibility matrix. A compatible tiny ligand does not establish that
all protein templates, metals or macrocycles are supported. Review preparation
warnings and run actual receptor/reference input tests before production.

## Install or repair guidance

Give commands as a proposed isolated environment, then run them only when the
current request authorizes installation. Preserve existing research environments.
Check current official package guidance and solve dependencies before pinning.
A starting recipe when conda/Miniforge is available is:

```powershell
conda create -n vina-work -c conda-forge python=3.11 rdkit meeko pdbfixer openmm
conda activate vina-work
python -m pip check
```

Channel/platform availability varies. If the solver cannot provide a package,
follow that project's supported installation route into this same environment;
do not mix random wheels or run bare pip from a different Python. Install the
official Vina CLI for the OS/architecture separately where necessary; `pip install
vina` may supply a Python API without the native executable used by this skill.
Record a solved environment with `conda env export --no-builds` or the selected
Python's `-m pip freeze`; do not call these locks portable across all platforms.

| Symptom | Suggested resolution |
|---|---|
| Python opens a store or is missing | Select real environment python.exe; avoid Windows app-execution alias |
| CLI found but cannot launch/DLL error | Check OS/architecture, trusted official binary, required runtime; preserve exact error |
| rdkit/meeko import or NumPy ABI error | Create a coherent isolated environment; avoid upgrading one binary dependency blindly |
| Meeko flags absent | Inspect that version's help; use compatible release or explicitly adapt command |
| OpenCL fails | Test available CPU/Reference platform; record platform, don't disable model checks |
| PowerShell policy blocks scripts | Use Python checker directly or approved signed/unblocked scripts; don't weaken global policy |
| Chinese/space/long paths fail in third-party tools | Quote arguments; stage copies in a short writable path and record hashes/mapping |
| Permission/antivirus/quarantine issue | Use a user-writable project folder; verify trusted package origin, do not disable protection |
| PyMOL absent or licensing unavailable | Complete docking and data outputs; defer visualization or use an available viewer |
| AutoGrid missing | Skip unrequested AD4; requested AD4 remains blocked until maps/tools are ready |

Sources: https://github.com/ccsb-scripps/AutoDock-Vina/releases ,
https://autodock-vina.readthedocs.io/ , https://meeko.readthedocs.io/ ,
https://www.rdkit.org/docs/Install.html , https://github.com/openmm/pdbfixer ,
https://docs.openmm.org/ . Consult current releases when installing; this skill
does not fetch executables or guarantee external package availability.
