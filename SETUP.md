# TokenGovernor Setup Guide

## Prerequisites

1. **GitHub Personal Access Token**
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate a new token with `repo` and `workflow` permissions
   - Copy the token

2. **Python Environment**
   ```bash
   pip install PyGithub python-dotenv
   ```

## Quick Setup

### Option 1: Automated Setup (Recommended)

1. **Set your GitHub token:**
   ```bash
   # Windows
   set GITHUB_TOKEN=your_token_here
   
   # Linux/Mac
   export GITHUB_TOKEN=your_token_here
   ```

2. **Run the setup script:**
   ```bash
   python scripts/setup_remote.py
   ```

This will:
- Create the GitHub repository
- Add remote origin
- Push the code
- Set up branch protection rules

### Option 2: Manual Setup

1. **Create repository on GitHub:**
   - Go to https://github.com/new
   - Repository name: `TokenGovernor`
   - Description: `Standalone governance system for agentic coding workflows`
   - Keep it public
   - Don't initialize with README (we have local files)

2. **Add remote and push:**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/TokenGovernor.git
   git branch -M main
   git push -u origin main
   ```

3. **Set up branch protection:**
   - Go to repository Settings → Branches
   - Add rule for `main` branch
   - Enable "Require status checks to pass before merging"
   - Enable "Require branches to be up to date before merging"

## Verification

After setup, verify everything works:

```bash
# Check remote
git remote -v

# Check branch
git branch -a

# Verify GitHub Actions
# Go to your repository → Actions tab
```

## Next Steps

1. Configure any additional GitHub secrets
2. Set up local development environment
3. Start implementing TokenGovernor features
4. Create your first feature branch and PR

## Troubleshooting

- **Permission denied**: Check your GitHub token has `repo` permissions
- **Repository exists**: The repository name might already be taken
- **Push rejected**: Make sure you don't have any conflicts

For more help, see the main README.md