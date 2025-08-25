@echo off
REM Windows-compatible pre-command hook for claude-flow
REM Input: %1 = command to validate

echo Pre-command validation for: %1
REM Add any Windows-specific validation logic here
exit /b 0