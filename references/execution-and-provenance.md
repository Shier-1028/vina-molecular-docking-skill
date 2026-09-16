# Execution, recovery, and evidence

## Plan and state

Count requested receptor x ligand-state x scorer x seed tasks explicitly; separate
screening jobs, validation runs, score-only and local-only diagnostics. Do not
count excluded or diagnostic tasks as completed production pairs.
Maintain statuses: prepared, validation_running, validated, validation_failed,
exploratory, queued, running, completed, invalid, interrupted, superseded.
Keep validation status separate from process completion status.

Use run-specific directories and explicit manifest paths. Avoid selecting the
first existing *_trimmed/*_merged file: it may belong to a superseded model.
Grid generation must not silently regenerate the receptor under its old name.
Snapshot inputs, final numeric config and SHA256 hashes before launching.
Record tool versions, receptor model/state, ligand list/order, scorer, seed,
CPU allocation, exact command, start/end timestamps, exit code, stdout/stderr,
and validation evidence tied to those hashes. Running jobs use immutable inputs.
Model repair must not leave an old preparation log describing the new receptor.

Keep project preparation scripts separate from the reusable skill; do not copy
case-specific chains, CIDs, grids or template deletions as global defaults.

## Background work on Windows

Use native --batch, grouping by receptor and scorer. Budget workers times CPUs
per worker against available cores; multiple cpu=1 workers can be reasonable,
but do not assume parallel runs will each retain full-machine speed.
For Python orchestration use argument arrays, explicit cwd and log files.
Prefer streaming stdout/stderr to binary files for long runs, then decode using
the producer's known encoding. For text capture set encoding explicitly; UTF-8
child output decoded as Windows GBK can lose logs in a reader thread even when
the child succeeds. Accept utf-8-sig when reading BOM-bearing JSON/CSV inputs.
Persist child PID AND creation time, command and run identity, not PID alone.
On Windows start background helpers hidden unless a visible console is wanted.

Inspect exit status, CPU-time changes, elapsed wall time, log timestamps and
validated outputs together. Buffered empty logs are not proof of a hang. CPU
activity is not proof of eventual success. Do not state that a 100% progress bar
means only disk writing remains. Convert CPU seconds to hours by dividing by
3600, and distinguish CPU time from wall time. ETA is an estimate from comparable
work; macrocycles, flexibility, box and worker count can dominate runtime.

Do not promise that jobs survive closing the host application merely because
Start-Process was used. Inspect host lifecycle/job-object behavior where possible;
parent PID alone proves neither survival nor termination. Save a restart manifest.
Use the host's supported monitor mechanism only when follow-up is requested.
Respect requests to explain cost/runtime before execution and any explicit wait
for approval; a pasted historical launch command is not a fresh execution request.

## Resume and publication gate

Before restarting, identify whether the original job still runs. Do not launch
duplicate writers into an active directory. Validate existing outputs against
the matching input/config/scorer/model hashes; timestamps alone are insufficient.
Resume only missing/invalid tasks with a fresh run identity; native batch supports
an explicit subset. Preserve interrupted, failed and superseded artifacts outside
the authoritative summary. Do not change scientific parameters merely to shorten
an unverified wait. Terminate only the exact authorized task, not all vina/python.

Require complete MODEL/ENDMDL pairs, one finite score per model, finite atom
coordinates and exact input serial/type correspondence for every returned pose.
Fewer poses than num_modes can be normal; num_modes is a maximum. A zero return
code or existence of *_out.pdbqt alone is insufficient. Cross-check summary scores
against PDBQT and expected state IDs. Use the included summarizer per receptor;
its `ok` means file/atom validation, not biological or redocking validation.
It does not verify provenance hashes or grid/chemistry itself.

Only validated current models enter the primary matrix. Failed validation and
explicit exploratory runs can have separate tables, including older preliminary
outputs; never silently reuse them after receptor repair. Report not-run/failed
cells as missing with reasons, not zero affinity. Extract one best pose for viewing,
retain all original modes, and load receptor plus ligand for complex images.
PDBQT viewers may guess bonds; use a chemically validated graph for presentation.

For vina/vinardo comparison validate each scorer, rank within receptor and scorer,
and compare paired ligands, rank correlation/top-k overlap and mapped poses.
State the denominator and tie handling. Shared scoring agreement is computational
sensitivity analysis, not independent validation. Raw energies across receptors
do not establish selectivity or a globally 'strongest compound'. Activity against
one protein does not establish a positive control for another protein.
