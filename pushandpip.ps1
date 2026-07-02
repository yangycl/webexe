param(
    [switch]$DryRun,
    [switch]$SkipUpload,
    [switch]$SkipPush,
    [string]$CommitMessage = "chore: release package"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDir

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [scriptblock]$Action
    )

    Write-Host "`n==> $Name" -ForegroundColor Cyan
    & $Action
}

Invoke-Step "Install packaging tools" {
    python -m pip install --upgrade build twine
}

Invoke-Step "Clean old build artifacts" {
    Remove-Item -Path .\build, .\dist -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Directory -Filter "*.egg-info" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

Invoke-Step "Type check with mypy" {
    python -m mypy .\webexe\builder.py
}

Invoke-Step "Build package" {
    python -m build
}

Invoke-Step "Validate package" {
    python -m twine check .\dist\*
}

if (-not $SkipUpload) {
    if ($DryRun) {
        Write-Host "Dry run: would upload dist artifacts to PyPI." -ForegroundColor Yellow
    }
    else {
        Invoke-Step "Upload package" {
            python -m twine upload --skip-existing .\dist\*
        }
    }
}

if (-not $SkipPush) {
    $gitStatus = git status --short
    if ([string]::IsNullOrWhiteSpace($gitStatus)) {
        Write-Host "No tracked changes to commit." -ForegroundColor Yellow
    }
    else {
        if ($DryRun) {
            Write-Host "Dry run: would commit and push changes." -ForegroundColor Yellow
        }
        else {
            git add .
            git commit -m $CommitMessage
            git push
        }
    }
}
