#!/usr/bin/env python3
"""Setup script for TokenGovernor GitHub remote repository"""

import os
import sys
import subprocess
import json
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from tokengovernor.github.repo_manager import GitHubRepoManager
except ImportError:
    print("❌ Error: Could not import GitHubRepoManager. Make sure PyGithub is installed.")
    print("Run: pip install PyGithub")
    sys.exit(1)


def check_git_status():
    """Check if we have uncommitted changes"""
    result = subprocess.run(['git', 'status', '--porcelain'], 
                          capture_output=True, text=True)
    if result.stdout.strip():
        print("⚠️  Warning: You have uncommitted changes:")
        print(result.stdout)
        return False
    return True


def setup_remote_repository():
    """Set up the remote GitHub repository"""
    print("🚀 Setting up TokenGovernor remote repository...")
    
    # Check for GitHub token
    if not os.getenv('GITHUB_TOKEN'):
        print("❌ GITHUB_TOKEN environment variable not set.")
        print("Please set your GitHub personal access token:")
        print("export GITHUB_TOKEN=your_token_here")
        return False
    
    # Load project config
    try:
        with open('project_config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ project_config.json not found. Run from project root directory.")
        return False
    
    # Create GitHub repository
    try:
        manager = GitHubRepoManager()
        clone_url = manager.create_repository(config)
        repo_name = config['repository']['name']
        
        print(f"✅ Repository created: {clone_url}")
        
        # Add remote origin
        subprocess.run(['git', 'remote', 'add', 'origin', clone_url], 
                      check=True)
        print("✅ Added remote origin")
        
        # Create and switch to main branch
        subprocess.run(['git', 'branch', '-M', 'main'], check=True)
        print("✅ Renamed branch to main")
        
        # Push to remote
        subprocess.run(['git', 'push', '-u', 'origin', 'main'], 
                      check=True)
        print("✅ Pushed to remote repository")
        
        # Set up branch protection (optional)
        try:
            manager.setup_branch_protection(repo_name, 'main')
        except Exception as e:
            print(f"⚠️  Could not set up branch protection: {e}")
            print("You can set this up manually in GitHub settings")
        
        print("\n🎉 GitHub repository setup complete!")
        print(f"Repository URL: https://github.com/{manager.user.login}/{repo_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up repository: {e}")
        return False


def main():
    """Main setup function"""
    print("TokenGovernor GitHub Setup")
    print("=" * 30)
    
    # Check git status
    if not check_git_status():
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Aborted. Please commit your changes first.")
            return
    
    # Setup remote repository
    if setup_remote_repository():
        print("\n✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Configure GitHub Actions secrets if needed")
        print("2. Set up development environment")
        print("3. Start implementing TokenGovernor features")
    else:
        print("\n❌ Setup failed. Please check the errors above.")


if __name__ == "__main__":
    main()