# Run inside ops-center project root

git init
git branch -M main
git add .
git commit -m "chore: initialize YEIP stable baseline"

git checkout -b develop
git checkout -b feature/v6.1-enterprise-ui

Write-Host "Git initialized. Current branch: feature/v6.1-enterprise-ui"
