param(
    [string]$RequirementsPath = "requirements.txt",
    [string]$WheelhousePath = "wheelhouse"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $RequirementsPath)) {
    throw "Requirements file not found: $RequirementsPath"
}

if (-not (Test-Path $WheelhousePath)) {
    New-Item -ItemType Directory -Path $WheelhousePath | Out-Null
}

Get-ChildItem -Path $WheelhousePath -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -ne ".gitkeep" } |
    Remove-Item -Force

python -m pip download `
    --dest $WheelhousePath `
    --only-binary=:all: `
    --platform manylinux2014_x86_64 `
    --implementation cp `
    --python-version 3.12 `
    --abi cp312 `
    -r $RequirementsPath

if ($LASTEXITCODE -ne 0) {
    throw "Failed to download wheels for Linux cp312."
}

# Some Linux-only transitive deps behind environment markers (for example uvloop)
# are skipped when resolving from a Windows host, so fetch them explicitly.
$forcedPackages = @("uvloop")
foreach ($pkg in $forcedPackages) {
    python -m pip download `
        --dest $WheelhousePath `
        --only-binary=:all: `
        --platform manylinux2014_x86_64 `
        --implementation cp `
        --python-version 3.12 `
        --abi cp312 `
        $pkg

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to download forced package: $pkg"
    }
}

Write-Host "Wheels downloaded to $WheelhousePath"
