Write-Host "========================================="
Write-Host " YEIP Git Init"
Write-Host "========================================="

if (-not (Test-Path ".git")) {
    git init
}

git checkout -B main
git add .
git commit -m "chore: initialize YEIP project foundation"

git checkout -B develop
git checkout -B feature/v6.1-enterprise-ui

Write-Host "========================================="
Write-Host " Git branches created:"
git branch
Write-Host "========================================="