# PowerShell post-command hook for claude-flow
param(
    [string]$Command
)

Write-Host "Post-command tracking for: $Command"
# Add any tracking logic here
exit 0