@echo off
echo Restarting PHANTOM Services...
docker compose restart
echo.
echo PHANTOM Services Restarted.
echo Dashboard: http://localhost:3000
