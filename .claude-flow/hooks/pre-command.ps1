# PowerShell pre-command hook for claude-flow
param(
    [string]$Command
)

Write-Host "Pre-command validation for: $Command"
# Add any validation logic here
exit 0