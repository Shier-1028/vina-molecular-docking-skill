param(
  [string]$PythonExe = 'python',
  [string]$VinaExe,
  [string]$MeekoPrepareReceptor,
  [string]$MeekoPrepareLigand,
  [ValidateSet('dock','prepare','validate','repair')][string]$Profile = 'dock',
  [string]$Config,
  [string]$Report = ('environment-check-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.json'),
  [string]$SaveConfig,
  [ValidateSet('vina','vinardo','ad4')][string]$Scoring = 'vina'
)
$ErrorActionPreference='Stop'
if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
  $found=Get-Command $PythonExe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $found) { throw 'Python not found. Install Python/Miniforge, activate its environment, or pass -PythonExe with the real executable path. See references/first-use.md.' }
  $PythonExe=$found.Source
}
$params=@((Join-Path $PSScriptRoot 'check_environment.py'),'--profile',$Profile,'--report',$Report,'--scoring',$Scoring)
if ($VinaExe) {$params+=@('--vina',$VinaExe)}
if ($MeekoPrepareReceptor) {$params+=@('--prepare-receptor',$MeekoPrepareReceptor)}
if ($MeekoPrepareLigand) {$params+=@('--prepare-ligand',$MeekoPrepareLigand)}
if ($Config) {$params+=@('--config',$Config)}
if ($SaveConfig) {$params+=@('--save-config',$SaveConfig)}
& $PythonExe @params
exit $LASTEXITCODE
