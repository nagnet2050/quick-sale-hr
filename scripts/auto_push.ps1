Param(
    [string]$RepoPath = (Resolve-Path "..\"),
    [string]$Branch = "main",
    [int]$IntervalSeconds = 10,
    [switch]$NoPull
)

<#
 .SYNOPSIS
    Simple auto-commit and auto-push watcher for Git repositories (Windows PowerShell).

 .DESCRIPTION
    Polls the Git working tree every N seconds. If there are any changes, it will:
      1) git add -A
      2) git commit -m "chore(auto): sync <timestamp>"
      3) git pull --rebase origin <branch>   (unless -NoPull is set)
      4) git push origin <branch>

    Notes:
    - Respects your .gitignore automatically via git add
    - Skips if there are no changes
    - Handles transient errors and keeps running

 .EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts/auto_push.ps1 -RepoPath . -Branch main -IntervalSeconds 10

 .EXIT
    Press Ctrl+C to stop.
#>

function Write-Log {
    param([string]$Message, [string]$Level = 'INFO')
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Write-Host "[$ts] [$Level] $Message"
}

try {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw "Git is not installed or not in PATH."
    }

    $RepoFullPath = (Resolve-Path $RepoPath).Path
    Set-Location $RepoFullPath
    Write-Log "Auto push started in: $RepoFullPath (branch: $Branch, interval: ${IntervalSeconds}s)"

    # Verify repository
    $gitTop = (git rev-parse --show-toplevel 2>$null)
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($gitTop)) {
        throw "Not a Git repository: $RepoFullPath"
    }

    # Ensure branch exists locally
    $currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()
    if ($currentBranch -ne $Branch) {
        Write-Log "Switching to branch '$Branch' (current: '$currentBranch')" "WARN"
        git checkout $Branch | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Failed to checkout branch '$Branch'" }
    }

    while ($true) {
        try {
            $status = git status --porcelain
            if ($LASTEXITCODE -ne 0) { throw "git status failed" }

            if ($status) {
                Write-Log "Changes detected. Committing..."
                git add -A | Out-Null
                if ($LASTEXITCODE -ne 0) { throw "git add failed" }

                $msg = "chore(auto): sync " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
                git commit -m $msg | Out-Null
                if ($LASTEXITCODE -ne 0) {
                    # Nothing to commit or another failure
                    $lastOut = $status | Out-String
                    Write-Log "Commit skipped or failed. Status: $lastOut" "WARN"
                }

                if (-not $NoPull) {
                    Write-Log "Rebasing with remote before push..."
                    git pull --rebase origin $Branch | Out-Null
                    if ($LASTEXITCODE -ne 0) { Write-Log "git pull --rebase failed" "WARN" }
                }

                Write-Log "Pushing to origin/$Branch..."
                git push origin $Branch | Out-Null
                if ($LASTEXITCODE -ne 0) { Write-Log "git push failed" "WARN" }
                else { Write-Log "Push completed." }
            }
        }
        catch {
            Write-Log $_.Exception.Message "ERROR"
        }

        Start-Sleep -Seconds $IntervalSeconds
    }
}
catch {
    Write-Log $_.Exception.Message "ERROR"
    exit 1
}
