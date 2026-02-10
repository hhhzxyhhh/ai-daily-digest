# Check if git is installed
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Git is not installed or not in your PATH." -ForegroundColor Red
    Write-Host "Please install Git from https://git-scm.com/downloads and try again."
    exit 1
}

# Initialize git repository
Write-Host "Initializing Git repository..." -ForegroundColor Cyan
git init

# Check if .gitignore exists
if (-not (Test-Path ".gitignore")) {
    Write-Host "Creating .gitignore..." -ForegroundColor Yellow
    # Create simple .gitignore content to avoid committing secrets
    ".env`n__pycache__/`n*.pyc`n.DS_Store" | Out-File ".gitignore" -Encoding utf8
}

# Add files
Write-Host "Adding files to staging area..." -ForegroundColor Cyan
git add .

# Commit
Write-Host "Committing files..." -ForegroundColor Cyan
git commit -m "Initial commit of AI Daily Digest Agent"

Write-Host "`nRepository initialized and files committed successfully!" -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "1. Create a new repository on GitHub: https://github.com/new"
Write-Host "2. Run the following commands (replace URL with your repo URL):"
Write-Host "   git remote add origin <YOUR_REPO_URL>"
Write-Host "   git branch -M main"
Write-Host "   git push -u origin main"
