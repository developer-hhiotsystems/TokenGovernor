@echo off
REM Windows-compatible post-command hook for claude-flow  
REM Input: %1 = command executed

echo Post-command tracking for: %1
REM Add any Windows-specific tracking logic here
exit /b 0