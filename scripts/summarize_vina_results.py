"""Validate native Vina batch outputs, extract best poses, and rank per scorer."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
import sys


FIELDS = [
    "job_id", "ligand_code", "scoring", "status", "rank_within_scoring",
    "best_affinity_kcal_mol", "best_mode", "best_rmsd_lb", "best_rmsd_ub",
    "mode_count", "ligand_pdbqt", "docked_poses", "best_pose", "error",
]


def atom_signature(lines) -> dict[int, str]:
    signature = {}
    for line in lines:
        if not line.startswith(("ATOM  ", "HETATM")):
            continue
        serial = int(line[6:11])
        if serial in signature:
            raise ValueError(f"Duplicate atom serial {serial}")
        xyz = [float(line[a:b]) for a, b in ((30, 38), (38, 46), (46, 54))]
        charge = float(line[70:76])
        if not all(math.isfinite(x) for x in xyz + [charge]):
            raise ValueError("Nonfinite coordinates or charge")
        atom_type = line[77:].strip()
        if not atom_type or len(atom_type.split()) != 1:
            raise ValueError("Missing or invalid PDBQT atom type")
        signature[serial] = atom_type
    if not signature:
        raise ValueError("No PDBQT atoms")
    return signature


def parse_poses(path: Path) -> list[dict]:
    poses = []
    block = None
    seen = set()
    for line in path.read_text(encoding="utf-8-sig").splitlines(keepends=True):
        if line.startswith("MODEL"):
            if block is not None:
                raise ValueError("Nested MODEL before ENDMDL")
            number = int(line.split()[1])
            if number in seen:
                raise ValueError("Duplicate MODEL number")
            seen.add(number)
            block = {"number": number, "lines": [line], "score": None, "atoms": 0}
        elif line.startswith("ENDMDL"):
            if block is None:
                raise ValueError("ENDMDL without MODEL")
            block["lines"].append(line)
            if block["score"] is None or not block["atoms"]:
                raise ValueError("Model lacks a score or atoms")
            block["signature"] = atom_signature(block["lines"])
            poses.append(block)
            block = None
        elif block is not None:
            block["lines"].append(line)
            if line.startswith("REMARK VINA RESULT:"):
                values = tuple(float(x) for x in line.split(":", 1)[1].split())
                if (len(values) != 3 or not all(math.isfinite(x) for x in values)
                        or values[1] < 0 or values[2] < values[1]):
                    raise ValueError("Invalid affinity/RMSD values")
                if block["score"] is not None:
                    raise ValueError("Duplicate score in model")
                block["score"] = values
            elif line.startswith(("ATOM  ", "HETATM")):
                xyz = [float(line[a:b]) for a, b in ((30, 38), (38, 46), (46, 54))]
                if not all(math.isfinite(x) for x in xyz):
                    raise ValueError("Nonfinite atom coordinates")
                block["atoms"] += 1
    if block is not None:
        raise ValueError("Truncated model: ENDMDL missing")
    if not poses:
        raise ValueError("No complete scored models")
    return poses


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def summarize(ligand_dir: Path, results_dir: Path, scorings: list[str]) -> int:
    if not ligand_dir.is_dir() or not results_dir.is_dir():
        raise ValueError("Input ligand directory and results directory must exist")
    ligands = sorted(
        (p for p in ligand_dir.iterdir() if p.is_file() and p.suffix == ".pdbqt"),
        key=lambda p: p.name,
    )
    if not ligands:
        raise ValueError("No lowercase .pdbqt inputs found (native directory mode)")
    if len({p.stem.casefold() for p in ligands}) != len(ligands):
        raise ValueError("Ligand stems must be unique, ignoring case on Windows")
    rows = []
    for scoring in dict.fromkeys(scorings):
        score_rows = []
        for ligand in ligands:
            docked = results_dir / scoring / f"{ligand.stem}_out.pdbqt"
            row = dict.fromkeys(FIELDS, "")
            row.update(job_id=f"{scoring}:{ligand.stem}", ligand_code=ligand.stem,
                       scoring=scoring, status="missing", mode_count=0,
                       ligand_pdbqt=str(ligand.resolve()), docked_poses=str(docked.resolve()))
            if not docked.is_file():
                row["error"] = "Expected native batch output missing"
            else:
                try:
                    expected = atom_signature(ligand.read_text(encoding="utf-8-sig").splitlines())
                    poses = parse_poses(docked)
                    if any(pose["signature"] != expected for pose in poses):
                        raise ValueError("Output atom serial/type set differs from input ligand")
                    best = min(poses, key=lambda pose: pose["score"][0])
                    affinity, lower, upper = best["score"]
                    destination = results_dir / "best_poses" / scoring / f"{ligand.stem}.pdbqt"
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_text("".join(best["lines"]), encoding="utf-8")
                    row.update(status="ok", best_affinity_kcal_mol=affinity,
                               best_mode=best["number"], best_rmsd_lb=lower,
                               best_rmsd_ub=upper, mode_count=len(poses),
                               best_pose=str(destination.resolve()))
                except (OSError, ValueError, IndexError) as error:
                    row.update(status="invalid", error=str(error))
            score_rows.append(row)
        valid = sorted((r for r in score_rows if r["status"] == "ok"),
                       key=lambda r: r["best_affinity_kcal_mol"])
        previous = None
        rank = 0
        for index, row in enumerate(valid, 1):
            if row["best_affinity_kcal_mol"] != previous:
                rank = index
            row["rank_within_scoring"] = rank
            previous = row["best_affinity_kcal_mol"]
        rows.extend(valid)
        rows.extend(r for r in score_rows if r["status"] != "ok")

    write_csv(results_dir / "docking_summary_all.csv", FIELDS, rows)
    comparison = {p.stem: {"ligand_code": p.stem} for p in ligands}
    comparison_fields = ["ligand_code"]
    for scoring in dict.fromkeys(scorings):
        comparison_fields.extend(f"{scoring}_{field}" for field in ("status", "score", "rank"))
    for row in rows:
        prefix = row["scoring"]
        comparison[row["ligand_code"]].update({
            f"{prefix}_status": row["status"],
            f"{prefix}_score": row["best_affinity_kcal_mol"],
            f"{prefix}_rank": row["rank_within_scoring"],
        })
    write_csv(results_dir / "scoring_comparison.csv", comparison_fields, list(comparison.values()))
    failures = sum(row["status"] != "ok" for row in rows)
    print(f"Validated {len(rows) - failures}/{len(rows)} ligand/scoring outputs. "
          f"Summaries: {results_dir.resolve()}")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ligand-dir", required=True, type=Path)
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--scoring", nargs="+", choices=("vina", "vinardo", "ad4"), default=["vina"])
    args = parser.parse_args()
    try:
        return summarize(args.ligand_dir, args.results_dir, args.scoring)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
