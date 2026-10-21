# Construit l'archive de l'extension dans versions\, avec le numéro de version
# lu dans blender_manifest.toml. L'archive est à plat : blender_manifest.toml
# et __init__.py doivent se trouver à sa racine pour que Blender l'installe.

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifest = Join-Path $root 'blender_manifest.toml'
$versions = Join-Path $root 'versions'

if (-not (Test-Path $manifest)) {
    throw "Manifeste introuvable : $manifest"
}

# --- version lue dans le manifeste ---
$version = '0.0.0'
foreach ($line in Get-Content $manifest) {
    if ($line -match '^\s*version\s*=\s*"([^"]+)"') {
        $version = $Matches[1]
        break
    }
}
$tag = 'v' + $version
Write-Host "Version : $tag"

# --- compilation ---
python -m py_compile (Join-Path $root '__init__.py')
if ($LASTEXITCODE -ne 0) {
    throw 'Échec de la compilation Python'
}
Write-Host 'Compilation : OK'

# --- mise en page à plat ---
New-Item -ItemType Directory -Path $versions -Force | Out-Null
$stage = Join-Path $env:TEMP ("propeller_" + $tag)
Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $stage | Out-Null

Copy-Item $manifest $stage
Copy-Item (Join-Path $root '__init__.py') $stage
Copy-Item (Join-Path $root 'README.md') $stage
Copy-Item (Join-Path $root 'LICENSE') $stage

Add-Type -AssemblyName System.IO.Compression.FileSystem
$name = "propeller_generator_$tag.zip"
$out = Join-Path $versions $name
if (Test-Path $out) { Remove-Item $out -Force }
[System.IO.Compression.ZipFile]::CreateFromDirectory($stage, $out)
Remove-Item $stage -Recurse -Force

$size = (Get-Item $out).Length
$hash = (Get-FileHash $out -Algorithm SHA256).Hash.Substring(0, 16)
Write-Host ''
Write-Host "Archive : versions\$name  ($size octets)"
Write-Host "SHA256 (16) : $hash"
