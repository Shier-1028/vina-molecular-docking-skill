from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


POLAR_TYPES = {"OA", "O", "N", "NA", "NS", "SA", "S"}


def parse_pdbqt(path: Path) -> list[dict[str, object]]:
    atoms: list[dict[str, object]] = []
    models = 0
    with path.open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if line.startswith("MODEL"):
                models += 1
                if models > 1:
                    raise ValueError("Contact analysis requires one extracted pose, not multiple models")
            if not line.startswith(("ATOM", "HETATM")):
                continue
            atom_type = line.split()[-1]
            if atom_type in {"H", "HD", "HS"} or (atom_type.startswith("G") and atom_type[1:].isdigit()):
                continue
            atoms.append(
                {
                    "serial": line[6:11].strip(),
                    "name": line[12:16].strip(),
                    "resn": line[17:20].strip(),
                    "chain": line[21:22].strip(),
                    "resi": line[22:27].strip(),
                    "x": float(line[30:38]),
                    "y": float(line[38:46]),
                    "z": float(line[46:54]),
                    "type": atom_type,
                }
            )
    return atoms


def distance(a: dict[str, object], b: dict[str, object]) -> float:
    return math.sqrt(
        (float(a["x"]) - float(b["x"])) ** 2
        + (float(a["y"]) - float(b["y"])) ** 2
        + (float(a["z"]) - float(b["z"])) ** 2
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize simple geometric receptor-ligand contacts from PDBQT.")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--receptor", required=True)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    receptor_atoms = parse_pdbqt(Path(args.receptor))
    if not receptor_atoms:
        raise ValueError("Receptor has no heavy atoms")
    receptor_polar = [a for a in receptor_atoms if str(a["type"]) in POLAR_TYPES]

    residue_rows: list[dict[str, object]] = []
    polar_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []

    with Path(args.summary).open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if row["status"] != "ok":
                continue
            ligand_atoms = parse_pdbqt(Path(row["best_pose"]))
            if not ligand_atoms:
                raise ValueError(f"Empty best pose: {row['best_pose']}")
            ligand_polar = [a for a in ligand_atoms if str(a["type"]) in POLAR_TYPES]

            residues: dict[tuple[str, str, str], float] = {}
            for ra in receptor_atoms:
                min_dist = min(distance(ra, la) for la in ligand_atoms)
                if min_dist <= 4.0:
                    key = (str(ra["chain"]), str(ra["resn"]), str(ra["resi"]))
                    residues[key] = min(min_dist, residues.get(key, 999.0))

            for chain, resn, resi in sorted(residues):
                residue_rows.append(
                    {
                        "job_id": row["job_id"],
                        "ligand_code": row["ligand_code"],
                        "chain": chain,
                        "resn": resn,
                        "resi": resi,
                        "min_distance_angstrom": f"{residues[(chain, resn, resi)]:.2f}",
                    }
                )

            seen_polar: set[tuple[str, str, str, str, str]] = set()
            for la in ligand_polar:
                for ra in receptor_polar:
                    dist = distance(la, ra)
                    if dist <= 3.6:
                        key = (
                            str(la["name"]),
                            str(ra["chain"]),
                            str(ra["resn"]),
                            str(ra["resi"]),
                            str(ra["name"]),
                        )
                        if key in seen_polar:
                            continue
                        seen_polar.add(key)
                        polar_rows.append(
                            {
                                "job_id": row["job_id"],
                                "ligand_code": row["ligand_code"],
                                "ligand_atom": la["name"],
                                "ligand_type": la["type"],
                                "receptor_chain": ra["chain"],
                                "receptor_resn": ra["resn"],
                                "receptor_resi": ra["resi"],
                                "receptor_atom": ra["name"],
                                "receptor_type": ra["type"],
                                "distance_angstrom": f"{dist:.2f}",
                            }
                        )

            summary_rows.append(
                {
                    "job_id": row["job_id"],
                    "ligand_code": row["ligand_code"],
                    "scoring": row["scoring"],
                    "energy": row["best_affinity_kcal_mol"],
                    "pocket_residue_count_4A": len(residues),
                    "geometric_polar_contact_count_3_6A": len(seen_polar),
                    "pocket_residues_4A": ";".join(
                        f"{chain}:{resn}{resi}" for chain, resn, resi in sorted(residues)
                    ),
                }
            )

    outputs = [
        (out_dir / "geometric_contact_summary.csv", summary_rows),
        (out_dir / "geometric_pocket_residues_4A.csv", residue_rows),
        (out_dir / "geometric_polar_contacts_3_6A.csv", polar_rows),
    ]
    for path, rows in outputs:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["empty"])
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    main()
