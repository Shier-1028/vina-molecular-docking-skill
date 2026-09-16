"""Validate global redocking RMSD with an explicit heavy-atom bijection; no fitting."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

from rdkit import Chem
from rdkit.Chem import rdMolAlign
from summarize_vina_results import atom_signature, parse_poses


def real_atoms(lines):
    result = {}
    for line in lines:
        if not line.startswith(("ATOM  ", "HETATM")):
            continue
        kind = line[77:].strip()
        if kind in {"H", "HD", "HS"} or (kind.startswith("G") and kind[1:].isdigit()):
            continue
        element = {"A": "C", "NA": "N", "NS": "N", "OA": "O", "OS": "O", "SA": "S"}.get(kind, kind)
        if kind.startswith("CG") and kind[2:].isdigit():
            element = "C"
        result[int(line[6:11])] = (element.upper(), tuple(float(line[a:b]) for a, b in ((30, 38), (38, 46), (46, 54))))
    return result


def evaluate(reference, input_path, map_path, outputs, threshold, fraction):
    if not math.isfinite(threshold) or threshold <= 0 or not 0 < fraction <= 1:
        raise ValueError("Invalid threshold or required pass fraction")
    if len({p.resolve() for p in outputs}) != len(outputs):
        raise ValueError("Duplicate output paths")
    mol = Chem.MolFromMolFile(str(reference), removeHs=True)
    if mol is None or not mol.GetNumAtoms() or mol.GetNumConformers() != 1:
        raise ValueError("Reference must contain one valid molecule and conformer")
    lines = input_path.read_text(encoding="utf-8-sig").splitlines()
    signature = atom_signature(lines)
    atoms = real_atoms(lines)
    pairs = json.loads(map_path.read_text(encoding="utf-8-sig"))
    if not isinstance(pairs, list) or any(not isinstance(p, list) or len(p) != 2 or any(type(x) is not int for x in p) for p in pairs):
        raise ValueError("Atom map must be a list of integer [reference_index, serial] pairs")
    n = mol.GetNumAtoms()
    if len(pairs) != n or {p[0] for p in pairs} != set(range(n)) or len({p[1] for p in pairs}) != n or {p[1] for p in pairs} != set(atoms):
        raise ValueError("Atom map is not a complete real-heavy-atom bijection")
    for i, serial in pairs:
        element, coord = atoms[serial]
        if element != mol.GetAtomWithIdx(i).GetSymbol().upper():
            raise ValueError("Atom map element mismatch")
        refcoord = tuple(mol.GetConformer().GetAtomPosition(i))
        if not all(math.isfinite(x) for x in refcoord) or math.dist(coord, refcoord) > 0.01:
            raise ValueError("Input/reference frame mismatch (>0.01 A); verify reference and map")
    matches = mol.GetSubstructMatches(mol, uniquify=False, useChirality=True, maxMatches=100001)
    if len(matches) >= 100001 or not matches:
        raise ValueError("Symmetry enumeration unavailable or truncated")
    maps = [[(i, j) for i, j in enumerate(match)] for match in matches]
    rows = []
    for path in outputs:
        row = {"output": str(path.resolve()), "status": "invalid"}
        try:
            poses = parse_poses(path)
            if poses[0]["number"] != 1 or any(p["signature"] != signature for p in poses):
                raise ValueError("Top model or input atom correspondence is invalid")
            if poses[0]["score"][0] > min(p["score"][0] for p in poses):
                raise ValueError("MODEL 1 is not the best-scored pose")
            rmsds = []
            for pose in poses:
                coords = real_atoms(pose["lines"])
                probe = Chem.Mol(mol)
                for i, serial in pairs:
                    probe.GetConformer().SetAtomPosition(i, coords[serial][1])
                rmsds.append(float(rdMolAlign.CalcRMS(probe, mol, map=maps)))
            best = min(range(len(rmsds)), key=rmsds.__getitem__)
            row.update(status="pass" if rmsds[0] <= threshold else "fail",
                       top1_rmsd_A=rmsds[0], top1_score=poses[0]["score"][0],
                       best_recovery_mode=poses[best]["number"], best_recovery_rmsd_A=rmsds[best],
                       output_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        except (OSError, ValueError, IndexError, KeyError) as error:
            row["error"] = str(error)
        rows.append(row)
    passed = sum(r["status"] == "pass" for r in rows)
    invalid = any(r["status"] == "invalid" for r in rows)
    eligible = not invalid and passed / len(rows) >= fraction
    return {"status": "pass" if eligible else "incomplete" if invalid else "unstable" if passed else "fail",
            "passed": passed, "requested": len(rows), "pass_fraction": passed / len(rows),
            "threshold_A": threshold, "required_pass_fraction": fraction,
            "heavy_atoms": n, "symmetry_maps": len(maps), "ligand_fitted": False,
            "reference_sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
            "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
            "atom_map_sha256": hashlib.sha256(map_path.read_bytes()).hexdigest(), "results": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-sdf", type=Path, required=True)
    parser.add_argument("--input-pdbqt", type=Path, required=True)
    parser.add_argument("--atom-map", type=Path, required=True)
    parser.add_argument("--outputs", type=Path, nargs="+", required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=2.0)
    parser.add_argument("--required-pass-fraction", type=float, default=1.0)
    args = parser.parse_args()
    inputs = [args.reference_sdf, args.input_pdbqt, args.atom_map, *args.outputs]
    if args.report.resolve() in {p.resolve() for p in inputs}:
        parser.error("Report must not overwrite an input")
    try:
        report = evaluate(args.reference_sdf, args.input_pdbqt, args.atom_map, args.outputs, args.threshold, args.required_pass_fraction)
    except (OSError, ValueError, RuntimeError) as error:
        report = {"status": "invalid_setup", "error": str(error)}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(report["status"])
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
