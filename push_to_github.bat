@echo off
set REPO_URL=https://github.com/smichalove/EMU_radiotelescope_classification.git

if not exist ".git" (
    echo Initializing Git repository...
    git init
    git remote add origin %REPO_URL%
) else (
    echo Updating remote URL...
    git remote set-url origin %REPO_URL%
)

echo Staging files...
git add .

echo Committing changes...
git commit -m "Automated update of EMU classifier"

echo Synchronizing with remote...
git branch -M main
git pull origin main --allow-unrelated-histories --no-edit

echo Pushing to GitHub...
git push -u origin main

echo Done!
pause