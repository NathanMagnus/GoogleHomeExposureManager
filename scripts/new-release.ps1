<#
.SYNOPSIS
    Creates a new release for Google Home Exposure Manager.

.DESCRIPTION
    This script bumps the version, commits, tags, and pushes a new release.
    It can also create a GitHub release if the GitHub CLI (gh) is installed.

.PARAMETER Version
    The new version number (e.g., "1.0.0" or "v1.0.0"). 
    If not provided, will auto-increment the patch version.

.PARAMETER Type
    The type of version bump: "major", "minor", or "patch" (default).
    Only used if Version is not provided.

.PARAMETER Message
    Optional release message/notes. If not provided, uses a default message.

.PARAMETER NoGitHubRelease
    Skip creating a GitHub release (just tag and push).

.EXAMPLE
    .\scripts\new-release.ps1 -Version 1.0.0
    
.EXAMPLE
    .\scripts\new-release.ps1 -Type minor -Message "Added new features"

.EXAMPLE
    .\scripts\new-release.ps1
    # Auto-increments patch version (0.1.0 -> 0.1.1)
#>

param(
    [string]$Version,
    [ValidateSet("major", "minor", "patch")]
    [string]$Type = "patch",
    [string]$Message,
    [switch]$NoGitHubRelease
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $RepoRoot) { $RepoRoot = Get-Location }

$ManifestPath = Join-Path $RepoRoot "custom_components\google_home_exposure_manager\manifest.json"

# Read current version
$Manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$CurrentVersion = $Manifest.version
Write-Host "Current version: $CurrentVersion" -ForegroundColor Cyan

# Determine new version
if ($Version) {
    $NewVersion = $Version -replace "^v", ""
} else {
    $Parts = $CurrentVersion -split "\."
    $Major = [int]$Parts[0]
    $Minor = [int]$Parts[1]
    $Patch = [int]$Parts[2]
    
    switch ($Type) {
        "major" { $Major++; $Minor = 0; $Patch = 0 }
        "minor" { $Minor++; $Patch = 0 }
        "patch" { $Patch++ }
    }
    $NewVersion = "$Major.$Minor.$Patch"
}

Write-Host "New version: $NewVersion" -ForegroundColor Green

# Confirm
$Confirm = Read-Host "Proceed with release v$NewVersion? (y/N)"
if ($Confirm -ne "y" -and $Confirm -ne "Y") {
    Write-Host "Aborted." -ForegroundColor Yellow
    exit 0
}

# Update manifest.json
$Manifest.version = $NewVersion
$Manifest | ConvertTo-Json -Depth 10 | Set-Content $ManifestPath -Encoding UTF8
Write-Host "✓ Updated manifest.json" -ForegroundColor Green

# Run tests
Write-Host "`nRunning tests..." -ForegroundColor Cyan
Push-Location $RepoRoot
try {
    pytest tests/ -v --tb=short
    if ($LASTEXITCODE -ne 0) {
        throw "Tests failed! Aborting release."
    }
    Write-Host "✓ Tests passed" -ForegroundColor Green
} finally {
    Pop-Location
}

# Git operations
Write-Host "`nCommitting and tagging..." -ForegroundColor Cyan
Push-Location $RepoRoot
try {
    git add custom_components/google_home_exposure_manager/manifest.json
    git commit -m "chore: bump version to $NewVersion"
    Write-Host "✓ Committed version bump" -ForegroundColor Green
    
    git tag "v$NewVersion"
    Write-Host "✓ Created tag v$NewVersion" -ForegroundColor Green
    
    git push origin main
    git push origin "v$NewVersion"
    Write-Host "✓ Pushed to origin" -ForegroundColor Green
} finally {
    Pop-Location
}

# Create GitHub release
if (-not $NoGitHubRelease) {
    $GhInstalled = Get-Command gh -ErrorAction SilentlyContinue
    if ($GhInstalled) {
        Write-Host "`nCreating GitHub release..." -ForegroundColor Cyan
        
        if (-not $Message) {
            $Message = "Release v$NewVersion"
        }
        
        Push-Location $RepoRoot
        try {
            gh release create "v$NewVersion" --title "v$NewVersion" --notes $Message
            Write-Host "✓ GitHub release created" -ForegroundColor Green
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "`n⚠ GitHub CLI (gh) not installed. Create release manually at:" -ForegroundColor Yellow
        Write-Host "  https://github.com/NathanMagnus/GoogleHomeExposureManager/releases/new?tag=v$NewVersion" -ForegroundColor Cyan
    }
}

Write-Host "`n🎉 Release v$NewVersion complete!" -ForegroundColor Green
