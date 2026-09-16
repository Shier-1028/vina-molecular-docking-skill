param(
  [string[]]$Roots = @(),
  [ValidateRange(0,8)][int]$MaxDepth = 3,
  [ValidateRange(1,50000)][int]$MaxDirectories = 2000
)
$ErrorActionPreference='Stop'
$names=@('vina.exe','vina','python.exe','python','python3','mk_prepare_receptor.exe','mk_prepare_receptor.py','mk_prepare_ligand.exe','mk_prepare_ligand.py','autogrid4.exe','pymol.exe')
$hits=@{}
foreach ($name in $names) {
  foreach ($cmd in @(Get-Command $name -CommandType Application -All -ErrorAction SilentlyContinue)) { $hits[$cmd.Source]='PATH' }
}
$queue=New-Object System.Collections.Queue
foreach ($root in $Roots) {
  $item=Get-Item -LiteralPath $root -ErrorAction Stop
  if (-not $item.PSIsContainer) {throw "Scan root is not a directory: $root"}
  if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {throw "Choose a physical directory, not a reparse-point root: $root"}
  $queue.Enqueue(@($item.FullName,0))
}
$visited=0
$skipped=0
while ($queue.Count -gt 0 -and $visited -lt $MaxDirectories) {
  $entry=$queue.Dequeue(); $visited++
  try {$children=@(Get-ChildItem -LiteralPath $entry[0] -ErrorAction Stop)} catch {$skipped++; continue}
  foreach ($item in $children) {
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {continue}
    if ($item.PSIsContainer) {
      if ($entry[1] -lt $MaxDepth) {$queue.Enqueue(@($item.FullName,($entry[1]+1)))}
    } elseif ($names -contains $item.Name) {$hits[$item.FullName]='selected-root'}
  }
}
[pscustomobject]@{
  candidates=@($hits.Keys | Sort-Object | ForEach-Object {[pscustomobject]@{path=$_;source=$hits[$_]}})
  directories_scanned=$visited; unreadable_directories=$skipped; limit_reached=($queue.Count -gt 0)
  note='Candidates only. Nothing executed. Confirm executable/environment choices before preflight. No recursive scan occurs unless Roots is supplied.'
} | ConvertTo-Json -Depth 5
