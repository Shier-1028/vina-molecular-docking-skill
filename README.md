# vina-molecular-docking

An agent skill for **preparing, validating, running, resuming and auditing AutoDock Vina molecular
docking on Windows** — with validation gates that refuse to report a failed redocking as a success.

It is instructions plus small helper scripts. It is **not** an installer, and it is **not** a
click-to-run docking application.

## What it is not

- It does not bundle Vina, Python, AutoGrid, PyMOL, structure databases or any commercial license.
- It does not install anything, edit PATH, or touch the registry.
- It does not decide your chemistry. Protonation, tautomers, altlocs, cofactors, metals, waters and
  grid placement remain scientific judgement calls that the skill forces you to record explicitly.

## Requirements

| Requested work | Dependencies |
|---|---|
| Dock prepared PDBQT files | Official AutoDock Vina CLI; Python >= 3.9 for result checks |
| Prepare ligands/receptors | RDKit and Meeko (with its CLI) in the selected Python environment |
| Crystal RMSD validation | RDKit with 3D, InChI and `CalcRMS` functionality |
| PDBFixer repair workflow | PDBFixer, OpenMM and a working platform |
| Images | PyMOL or another viewer (optional) |
| AD4 scoring | AutoGrid4 plus matching receptor maps (optional, separately configured) |

One coherent Python environment should provide RDKit/Meeko; the checker binds to the interpreter you
select and records module versions and locations. A GPU, CUDA, MGLTools, Open Babel or conda is not
universally required.

## Install

Copy the `vina-molecular-docking/` directory into your agent's skills folder. There is no installer
and no guaranteed post-install hook: on first invocation the skill shows an onboarding checklist and
asks for software paths or permission to scan named folders. First run on a new machine should follow
[`references/first-use.md`](references/first-use.md).

## Quick start

```powershell
$skill = '<path to this directory>'

# 1. Candidate discovery: PATH only by default; nothing is executed.
& "$skill/scripts/find_tools.ps1"
& "$skill/scripts/find_tools.ps1" -Roots 'C:/Tools','E:/Miniforge/envs' -MaxDepth 3   # only after you authorize these roots

# 2. Capability checks in your chosen interpreter (not just version strings)
& 'C:/path/to/python.exe' "$skill/scripts/check_environment.py" --profile dock --vina 'C:/path/to/vina.exe' --report environment-dock.json --save-config local-tools.json
& 'C:/path/to/python.exe' "$skill/scripts/check_environment.py" --profile validate --config local-tools.json --report environment-validate.json

# 3. Native batch docking (one receptor/map load per batch; fresh output dir per run)
& $vina --receptor receptor.pdbqt --config conf.txt --batch ligands --dir results/run01/vina --scoring vina > results/run01/vina.log 2>&1

# 4. Strict summaries: missing or truncated outputs are errors, never zero scores
& 'C:/path/to/python.exe' "$skill/scripts/summarize_vina_results.py" --ligand-dir ligands --results-dir results/run01 --scoring vina vinardo
```

Full workflow, AD4 branch and reporting templates: [`references/workflow.md`](references/workflow.md).

## What's inside

```text
SKILL.md                              entry point: 9-step workflow and interpretation rules
agents/openai.yaml                    display name and default prompt for agent hosts
references/first-use.md               dependencies, path discovery, install/repair guidance
references/workflow.md                native Vina 1.2.7 CLI workflow on Windows (+ AD4 maps branch)
references/preparation-and-validation.md   chemistry, repair, grid coverage, redocking gates
references/execution-and-provenance.md     job accounting, Windows background runs, resume gates
references/project-template.md        directory convention and minimum manifests
references/report-template.md         methods/results/interpretation report skeleton
references/case-lessons.md            lessons re-derived from one historical docking session
references/distribution-review.md     portability fixes and known limits of this package
assets/project-template.json          configurable project manifest (all example values)
scripts/check_environment.py          capability probe -> JSON report, no installation
scripts/check_vina_env.ps1            PowerShell wrapper for the checker
scripts/find_tools.ps1                bounded, opt-in tool discovery (reports candidates only)
scripts/summarize_vina_results.py     validates outputs, extracts best poses, ranks per scorer
scripts/summarize_geometric_contacts.py   pocket/polar contacts on a single extracted pose
scripts/validate_redocking.py         unfitted, symmetry-corrected heavy-atom RMSD via explicit atom map
```

## Design principles

- **A process, a progress bar, a file and an exit code are four different kinds of evidence.** None
  of them alone establishes validated completion. Vina can skip a malformed ligand with exit code 0.
- **Validation gates production.** Each receptor/scorer/preparation/box combination is validated by
  global co-crystal redocking (top-1, unfitted, symmetry-corrected heavy-atom RMSD; a common
  predeclared rule is `<= 2 Å` across three seeds). Mixed seeds are reported as unstable. Unvalidated
  work may continue only if it is explicitly labelled exploratory.
- **Scoring functions are separate searches.** `vina`, `vinardo` and `ad4` results are compared by
  rank stability, atom-matched poses and contacts — never pooled or averaged into one global ranking.
- **Vina's RMSD bounds are relative to the run's own best pose**, not to a crystal pose and not
  across scoring functions. Fixed-pose rescoring (`--score_only`) is not a redocking.
- **Provenance is part of the result.** Input hashes, frozen config, ligand order, scorer, seed, CPU
  allocation, command, timestamps and exit status are recorded before a launch and tied to the outputs.
- **Never loosen a threshold to make a run pass.** Failed and exploratory artifacts are preserved and
  reported separately, not silently promoted or reused after a receptor repair.

## Tested scope and known limitations

Windows is the tested platform. The Python checker adapts to Linux/macOS but was not exercised there.
Directory-mode batch behaviour is documented for Vina 1.2.7 and must not be assumed for other
releases — other versions are probed for actual CLI capabilities and then require a real-input smoke
run plus redocking. A passing environment check does not imply that every protein template, metal,
non-standard residue or macrocycle is supported; Meeko behaviour must be tested with real inputs.
See [`references/distribution-review.md`](references/distribution-review.md) for the full list.

## 中文简介

这是一个用于 **AutoDock Vina 分子对接**的智能体 skill，覆盖准备、验证、执行、续跑与审计全过程，
面向 Windows 平台。它由指令文档和若干辅助脚本组成，**不包含也不安装任何软件**（Vina、Python、
AutoGrid、PyMOL、数据库结构、商业授权均不捆绑），不会修改 PATH 或注册表，也不会替你做化学判断。

它真正的价值在于**证据纪律**：把"进程在跑""进度条 100%""文件存在""退出码为 0"当作四类不同的
证据；要求对接前用共晶配体重对接通过验证闸门（top-1、不拟合、对称校正重原子 RMSD，常用预声明
标准为三个随机种子均 `<= 2 Å`），未通过则只能标注为探索性工作；要求把输入哈希、冻结配置、配体
顺序、打分函数、随机种子、CPU 分配、命令与时间戳一并留档；`vina`/`vinardo`/`ad4` 三种打分只比较
排序稳定性与姿态一致性，**不做原始分数的跨函数混合排名或平均**；失败与探索性结果单独保留、不因
修复受体而被静默复用。

脚本：环境能力检查（`check_environment.py`，输出 JSON 报告，绝不自动安装）、受限工具发现
（`find_tools.ps1`，默认只查 PATH，需授权才扫描指定目录）、批处理结果汇总
（`summarize_vina_results.py`，缺失或截断的输出按错误处理而非记 0 分）、几何接触统计、以及
需要显式原子映射的重对接 RMSD 校验（`validate_redocking.py`）。

已知边界：Windows 为实测平台；AD4 需要匹配的 AutoGrid 映射；环境检查通过不等于所有结构都能处理；
本包是工作流与辅助脚本，不是全自动对接软件。

## License

Not yet chosen — see the repository license file. `references/case-lessons.md` is derived from one
historical session and is provided as examples to assess, not as authorization or endorsement.
