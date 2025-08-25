# TokenGovernor Documentation

## 📚 Documentation Index

### 🚀 Getting Started
- [Main README](../README.md) - Project overview and quick start
- [Setup Guide](../SETUP.md) - Installation and configuration  

### 🛠️ Troubleshooting & CI/CD
- [**GitHub CI/CD Troubleshooting Guide**](GITHUB_CICD_TROUBLESHOOTING.md) - Comprehensive troubleshooting guide
- [**Quick CI Fixes**](QUICK_CI_FIXES.md) - 30-second fixes for common issues
- [Architecture Overview](ARCHITECTURE.md) - System design and components *(coming soon)*

### 📖 API Documentation  
- [REST API Reference](API.md) - API endpoints and schemas *(coming soon)*
- [CLI Commands](CLI.md) - Command-line interface guide *(coming soon)*

### 🔧 Development
- [Contributing Guidelines](CONTRIBUTING.md) - Development workflow *(coming soon)*
- [Testing Guide](TESTING.md) - Running and writing tests *(coming soon)*

---

## 🎯 Most Useful Resources

### For New Projects
1. **[Quick CI Fixes](QUICK_CI_FIXES.md)** - Essential for any Python + GitHub Actions setup
2. **[GitHub CI/CD Troubleshooting](GITHUB_CICD_TROUBLESHOOTING.md)** - Deep dive into common issues

### For TokenGovernor Development
1. **[Main README](../README.md)** - Start here for project overview
2. **[Setup Guide](../SETUP.md)** - Get the system running locally

---

## 📋 Quick Reference

### Essential Commands
```bash
# Setup
pip install -r requirements.txt
python run_api.py

# Testing  
pytest tests/ -v

# GitHub Actions
gh pr checks <PR_NUMBER>
gh run view --log-failed
```

### Common Issues
- **Dependencies fail?** → Check [Quick CI Fixes](QUICK_CI_FIXES.md#1-dependency-installation-fails)
- **Tests missing?** → Check [Quick CI Fixes](QUICK_CI_FIXES.md#4-missing-tests-directory)  
- **Can't merge PR?** → Check [Quick CI Fixes](QUICK_CI_FIXES.md#8-cannot-merge-pr-branch-protection)

---

*This documentation is living and evolving with the project. Contributions welcome!*