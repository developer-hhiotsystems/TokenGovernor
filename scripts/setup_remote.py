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
    print("Error: Could not import GitHubRepoManager. Make sure PyGithub is installed.")
    print("Run: pip install PyGithub")
    sys.exit(1)


def check_git_status():
    """Check if we have uncommitted changes"""
    result = subprocess.run(['git', 'status', '--porcelain'], 
                          capture_output=True, text=True)
    if result.stdout.strip():
        print("Warning: You have uncommitted changes:")
        print(result.stdout)
        return False
    return True


def setup_remote_repository(use_ssh: bool = True):
    """Set up the remote GitHub repository"""
    print("Setting up TokenGovernor remote repository...")
    print(f"Using {'SSH' if use_ssh else 'HTTPS'} for Git operations")
    
    # Check for GitHub token
    if not os.getenv('GITHUB_TOKEN'):
        print("GITHUB_TOKEN environment variable not set.")
        print("Please set your GitHub personal access token:")
        print("export GITHUB_TOKEN=your_token_here")
        return False
    
    # If using SSH, check for SSH key
    if use_ssh:
        ssh_test = subprocess.run(['ssh', '-T', 'git@github.com'], 
                                capture_output=True, text=True)
        if "successfully authenticated" not in ssh_test.stderr:
            print("SSH key not configured or not working with GitHub")
            print("Either:")
            print("1. Set up SSH key: https://docs.github.com/en/authentication/connecting-to-github-with-ssh")
            print("2. Use HTTPS instead by running: python scripts/setup_remote.py --https")
            return False
    
    # Load project config
    try:
        with open('project_config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("project_config.json not found. Run from project root directory.")
        return False
    
    # Create GitHub repository
    try:
        manager = GitHubRepoManager()
        clone_url, html_url = manager.create_repository(config, use_ssh=use_ssh)
        repo_name = config['repository']['name']
        
        print(f"Repository created: {html_url}")
        print(f"Clone URL: {clone_url}")
        
        # Add remote origin
        subprocess.run(['git', 'remote', 'add', 'origin', clone_url], 
                      check=True)
        print("Added remote origin")
        
        # Create and switch to main branch
        subprocess.run(['git', 'branch', '-M', 'main'], check=True)
        print("Renamed branch to main")
        
        # Push to remote
        subprocess.run(['git', 'push', '-u', 'origin', 'main'], 
                      check=True)
        print("Pushed to remote repository")
        
        # Set up branch protection (optional)
        try:
            manager.setup_branch_protection(repo_name, 'main')
        except Exception as e:
            print(f"Could not set up branch protection: {e}")
            print("You can set this up manually in GitHub settings")
        
        print("\nGitHub repository setup complete!")
        print(f"Repository URL: {html_url}")
        
        return True
        
    except Exception as e:
        print(f"Error setting up repository: {e}")
        return False


def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Set up TokenGovernor GitHub repository')
    parser.add_argument('--https', action='store_true', 
                       help='Use HTTPS instead of SSH for Git operations')
    parser.add_argument('--token', type=str,
                       help='GitHub personal access token')
    parser.add_argument('--force', action='store_true',
                       help='Skip confirmation prompts')
    args = parser.parse_args()
    
    # Set token if provided
    if args.token:
        os.environ['GITHUB_TOKEN'] = args.token
    
    use_ssh = not args.https
    
    print("TokenGovernor GitHub Setup")
    print("=" * 30)
    
    # Check git status
    if not check_git_status() and not args.force:
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Aborted. Please commit your changes first.")
            return
    
    # Setup remote repository
    if setup_remote_repository(use_ssh=use_ssh):
        print("\nSetup completed successfully!")
        print("\nNext steps:")
        print("1. Configure GitHub Actions secrets if needed")
        print("2. Set up development environment")
        print("3. Start implementing TokenGovernor features")
    else:
        print("\nSetup failed. Please check the errors above.")


if __name__ == "__main__":
    main()