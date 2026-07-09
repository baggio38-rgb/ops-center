Write-Host "========================================="
Write-Host " YEIP Project Check"
Write-Host "========================================="
python -m compileall .
Write-Host ""
Write-Host "Git status:"
git status
Write-Host "========================================="
