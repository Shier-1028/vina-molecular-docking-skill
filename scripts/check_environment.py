"""Capability checks in the selected Python environment. No software is installed."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

PROFILES = {'dock': [], 'prepare': ['rdkit', 'meeko'], 'validate': ['rdkit'],
            'repair': ['rdkit', 'meeko', 'pdbfixer', 'openmm']}


def resolve(value):
    path = Path(value).expanduser()
    found = str(path.resolve()) if path.is_file() else shutil.which(value)
    return str(Path(found).resolve()) if found else None


def run(command, timeout):
    try:
        p = subprocess.run(command, capture_output=True, timeout=timeout, shell=False)
        return p.returncode, (p.stdout + p.stderr).decode('utf-8', errors='replace')[-16000:]
    except (OSError, subprocess.TimeoutExpired) as error:
        return -1, str(error)


def inspect(profile, tools, timeout, scoring='vina'):
    checks = []
    resolved = {'python': str(Path(sys.executable).resolve())}

    def add(name, status, detail, remedy=''):
        checks.append(dict(name=name, status=status, detail=detail, remedy=remedy))

    add('python', 'pass' if sys.version_info >= (3, 9) else 'fail', sys.version,
        'Use Python >=3.9; an isolated Python 3.11 environment is a conservative starting point.' if sys.version_info < (3, 9) else '')
    if profile == 'dock':
        path = resolve(tools.get('vina', 'vina'))
        if not path:
            add('vina', 'fail', 'Executable not found', 'Install the official Vina binary and supply its absolute path. The Python vina package may not provide this CLI.')
        else:
            resolved['vina'] = path
            code, version = run([path, '--version'], timeout)
            hc, helptext = run([path, '--help'], timeout)
            required = ['--batch', '--dir', '--receptor', '--ligand', '--config', '--scoring', '--seed', '--cpu']
            if scoring == 'ad4':
                required.append('--maps')
            missing = [flag for flag in required if not re.search(re.escape(flag) + r'\b', helptext)]
            matched = re.search(r'AutoDock Vina\s+v?(\d+\.\d+\.\d+)', version, re.I)
            if code or hc or missing or scoring not in helptext or not matched:
                add('vina', 'fail', {'version': version, 'missing_flags': missing, 'help_exit': hc}, 'Official Vina 1.2.7 is a tested CLI baseline. Check release/architecture and native batch capabilities. Do not silently substitute AutoDock4 or smina.')
            else:
                baseline = matched.group(1) == '1.2.7'
                add('vina', 'pass' if baseline else 'warning', {'version': version.strip(), 'sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(), 'capability_check': 'passed'}, 'This version passed CLI checks but is not the tested baseline. Run a small input smoke job and reference redocking before production.' if not baseline else '')
    modules = PROFILES[profile]
    for module in modules:
        probe = "import importlib,importlib.metadata as md,json; m=importlib.import_module(%r); print(json.dumps({'module':m.__name__,'version':md.version(%r),'file':getattr(m,'__file__',None)}))" % (module, module)
        code, output = run([sys.executable, '-c', probe], timeout)
        add(module, 'pass' if code == 0 else 'fail', output.strip(),
            'Install this dependency into this exact Python environment. Inspect missing DLL/ABI or package-metadata errors; see first-use.md.' if code else '')
    if 'rdkit' in modules:
        code, output = run([sys.executable, '-c', "from rdkit import Chem; from rdkit.Chem import AllChem,rdMolAlign; m=Chem.AddHs(Chem.MolFromSmiles('CCO')); assert AllChem.EmbedMolecule(m,randomSeed=1)==0; assert Chem.MolToInchiKey(m); assert rdMolAlign.CalcRMS(m,m)<1e-8; print('RDKit 3D/InChI/RMSD smoke passed')"], timeout)
        add('rdkit_features', 'pass' if code == 0 else 'fail', output.strip(), 'Install a compatible complete RDKit build; import alone is insufficient.' if code else '')
    if 'meeko' in modules:
        for name, default, flags in [('prepare_receptor', 'mk_prepare_receptor', ['--read_pdb', '-o', '-p']), ('prepare_ligand', 'mk_prepare_ligand', ['-i', '-o'])]:
            value = tools.get(name)
            if not value:
                candidates = [Path(sys.executable).parent/'Scripts'/(default+'.exe'), Path(sys.executable).parent/default, Path(sys.executable).parent/(default+'.py')]
                value = next((str(p) for p in candidates if p.is_file()), default)
            path = resolve(value)
            if path:
                resolved[name] = path
                command = [sys.executable, path] if path.lower().endswith('.py') else [path]
                code, output = run(command + ['--help'], timeout)
                missing = [flag for flag in flags if not re.search(r'(?<!\w)' + re.escape(flag) + r'\b', output)]
                add(name, 'fail' if code or missing else 'pass', {'path':path,'missing_flags':missing,'output':output if code else 'CLI help passed'}, 'Use the Meeko CLI associated with this Python. Read its help before adapting a different interface.' if code or missing else '')
                if Path(path).parent not in [Path(sys.executable).parent, Path(sys.executable).parent/'Scripts']:
                    add(name+'_environment', 'warning', path, 'CLI is outside the selected Python prefix; verify its environment/version before preparation.')
            else:
                add(name, 'fail', 'Not found', 'Provide the Meeko executable or .py entry point, or install Meeko in the selected environment.')
        code, output = run([sys.executable, '-c', "from rdkit import Chem; from rdkit.Chem import AllChem; from meeko import MoleculePreparation,PDBQTWriterLegacy; m=Chem.AddHs(Chem.MolFromSmiles('CCO')); assert AllChem.EmbedMolecule(m,randomSeed=1)==0; setup=MoleculePreparation().prepare(m)[0]; text,ok,error=PDBQTWriterLegacy.write_string(setup); assert ok,error; assert 'ROOT' in text; print('Meeko ligand preparation smoke passed')"], timeout)
        add('meeko_features','pass' if code == 0 else 'fail',output.strip(),'Use mutually compatible Meeko/RDKit builds; see first-use.md.' if code else '')
    if 'openmm' in modules:
        code, output = run([sys.executable,'-c',"import openmm as mm; from pdbfixer import PDBFixer; s=mm.System(); s.addParticle(1); i=mm.VerletIntegrator(0.001); c=mm.Context(s,i,mm.Platform.getPlatformByName('CPU')); c.setPositions([[0,0,0]]); print('OpenMM CPU context passed')"], timeout)
        add('openmm_cpu','pass' if code == 0 else 'fail',output.strip(),'Check OpenMM runtime/plugins. CPU can avoid a broken OpenCL stack; GPU is not required.' if code else '')
    return {'schema_version':1,'checked_at':datetime.now(timezone.utc).isoformat(),'platform':sys.platform,'profile':profile,'scoring':scoring,'tools':resolved,'checks':checks,'ready':not any(x['status']=='fail' for x in checks),'scope':'Environment preflight only. Actual inputs, chemistry, map compatibility and redocking require separate validation.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile', choices=PROFILES, default='dock')
    p.add_argument('--config', type=Path)
    p.add_argument('--vina')
    p.add_argument('--prepare-receptor')
    p.add_argument('--prepare-ligand')
    p.add_argument('--scoring',choices=['vina','vinardo','ad4'],default='vina')
    p.add_argument('--timeout',type=float,default=45)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--save-config',type=Path)
    a=p.parse_args()
    if a.timeout <= 0: p.error('Timeout must be positive')
    destinations=[a.report]+([a.save_config] if a.save_config else [])
    if len({x.resolve() for x in destinations}) != len(destinations) or any(x.exists() for x in destinations):
        p.error('Choose fresh report/config paths; existing files will not be overwritten')
    try:
        config=json.loads(a.config.read_text(encoding='utf-8-sig')) if a.config else {}
        if not isinstance(config,dict): raise ValueError('Config must be a JSON object')
        tools=config.get('tools',{})
        if not isinstance(tools,dict) or any(not isinstance(v,str) for v in tools.values()): raise ValueError('tools must map names to path strings')
        if tools.get('python') and resolve(tools['python']) != str(Path(sys.executable).resolve()): raise ValueError('Run with the Python recorded in config, or select a new config')
        for key in ['vina','prepare_receptor','prepare_ligand']:
            if getattr(a,key): tools[key]=getattr(a,key)
        report=inspect(a.profile,tools,a.timeout,a.scoring)
    except (OSError,ValueError) as error:
        p.error(str(error))
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,indent=2),encoding='utf-8')
    for c in report['checks']:
        print(c['status'].upper()+': '+c['name'])
        if c['remedy']: print('  '+c['remedy'])
    if a.save_config and report['ready']:
        a.save_config.parent.mkdir(parents=True,exist_ok=True)
        a.save_config.write_text(json.dumps({'schema_version':1,'tools':dict(tools,**report['tools'])},indent=2),encoding='utf-8')
    print('Report: '+str(a.report.resolve()))
    return 0 if report['ready'] else 1


if __name__ == '__main__':
    sys.exit(main())
