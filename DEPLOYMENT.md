# Git Setup and Deployment Guide

## Files to Push to GitHub

### Required Files (Core Application)

```
FaceFinder/
├── src/
│   ├── __init__.py
│   ├── app.py                 [INCLUDE] - Main Flask application
│   └── db_config.py           [INCLUDE] - Database configuration
├── config/
│   ├── __init__.py
│   └── settings.py            [INCLUDE] - Application settings
├── static/                    [INCLUDE] - Web assets
├── templates/                 [INCLUDE] - HTML templates
├── docs/                      [INCLUDE] - Documentation
├── tests/                     [INCLUDE] - Test scripts
├── .gitignore                 [INCLUDE] - Git ignore rules
├── .gitattributes             [INCLUDE] - Git attributes
├── requirements.txt           [INCLUDE] - Python dependencies
├── .env.example               [INCLUDE] - Environment template
├── README.md                  [INCLUDE] - Project documentation
├── CONTRIBUTING.md            [INCLUDE] - Contribution guidelines
├── LICENSE                    [INCLUDE] - MIT License
└── INTEGRATION_SUMMARY.txt    [INCLUDE] - Integration status
```

### Files to EXCLUDE from Git (Already configured in .gitignore)

```
.env                          - Sensitive credentials
.venv/                        - Virtual environment
__pycache__/                  - Python cache
*.pkl                         - Embedding cache files
*.db                          - SQLite database
uploads/                      - Temporary uploads
test_*.jpg                    - Test images
*.pyc                         - Compiled Python files
face_recognition_log.txt      - Log files
IMPLEMENTATION_COMPLETE.md    - Temporary documentation
VERIFICATION_COMPLETE.md      - Temporary documentation
INTEGRATION_STATUS.md         - Temporary documentation
trustworthy_face_matcher.py   - Generated file
validate_trustworthy_matcher.py - Test file
verify_integration.py         - Verification script
```

## Step-by-Step Git Setup

### 1. Initialize or Link to Existing Repository

If starting fresh:

```bash
git init
git remote add origin https://github.com/Nishant5810/FaceFinder.git
```

If already initialized:

```bash
git remote -v  # Check existing remotes
```

### 2. Configure Git User (First Time Only)

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 3. Check What Will Be Committed

```bash
git status
```

This should show:

- **Green (Staged)**: Files ready to commit
- **Red (Untracked)**: Files not in repository yet
- **Ignored**: Files in .gitignore (won't appear)

### 4. Stage All Changes

```bash
git add .
```

Or stage specific files:

```bash
git add src/ config/ docs/ requirements.txt README.md
```

### 5. Create Initial Commit

```bash
git commit -m "Initial commit: FaceFinder face recognition system

- Multi-feature face matching engine
- Flask web interface
- Database configuration (MySQL/SQLite)
- Comprehensive documentation
- Testing framework
- MIT License"
```

### 6. Push to GitHub

```bash
# For the first time (sets upstream)
git push -u origin main

# For subsequent pushes
git push origin main
```

## Workflow for Updates

### When Making Changes:

```bash
# Check status
git status

# Stage changes
git add .

# Commit with clear message
git commit -m "Brief description of changes"

# Push to GitHub
git push
```

### Branch Workflow for Features:

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Add new feature description"

# Push branch
git push origin feature/new-feature

# Create Pull Request on GitHub website
```

## Important Security Notes

1. **Never commit `.env` file** - It contains sensitive data
   - Use `.env.example` as a template instead
   - Each developer creates their own `.env`

2. **Verify `.gitignore` is working**:

```bash
git check-ignore -v .env
git check-ignore -v embeddings_trustworthy.pkl
```

3. **If you accidentally commit a secret**:

```bash
# Remove from history (advanced)
git filter-branch --tree-filter 'rm -f .env' HEAD

# Or just create a new commit removing it
rm .env
git add .
git commit -m "Remove sensitive .env file"
```

## Verify Your Repository

After pushing, verify on GitHub:

1. Visit https://github.com/Nishant5810/FaceFinder
2. Check the files listed match what you intended
3. Verify `.env` and cache files are NOT present
4. Check `requirements.txt` is present

## Size Considerations

Use `git ls-files` to check file sizes:

```bash
git ls-files -s | awk '{print $4}' | xargs -I {} du -sh {}
```

Remove large files if needed:

```bash
# Find large files
find . -size +5M -type f
```

## GitHub Repository Structure

Your repository will have:

- **Main branch**: Production-ready code
- **Feature branches**: For new features (create via Pull Requests)
- **Documentation**: README, CONTRIBUTING, docs folder
- **Tests**: tests folder for test scripts

## Next Steps

1. Verify all files pushed correctly
2. Add collaborators if needed (Settings > Collaborators)
3. Enable branch protection (Settings > Branches)
4. Set up GitHub Actions for CI/CD (optional)

## Troubleshooting

### Changes not showing on GitHub

```bash
# Verify remote is correct
git remote -v

# Check recent commits
git log --oneline -5

# Force push if absolutely necessary (use carefully)
git push origin main --force
```

### Forgot to add file to .gitignore

```bash
# Remove from git tracking but keep local file
git rm --cached filename
git commit -m "Remove filename from tracking"

# Add to .gitignore
echo "filename" >> .gitignore
git add .gitignore
git commit -m "Add filename to .gitignore"
git push
```

### Want to revert recent commits

```bash
# See commit history
git log --oneline

# Revert last commit but keep changes
git reset --soft HEAD~1

# Revert and discard changes
git reset --hard HEAD~1
```
