"""GitHub Repository Manager for TokenGovernor"""
import os
from github import Github
from typing import Dict, Any, Optional
import json


class GitHubRepoManager:
    """Manages GitHub repository creation and configuration"""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize with GitHub token"""
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable.")
        self.github = Github(self.token)
        self.user = self.github.get_user()
    
    def create_repository(self, config: Dict[str, Any]) -> str:
        """Create a new GitHub repository based on project config"""
        repo_config = config.get('repository', {})
        
        repo = self.user.create_repo(
            name=repo_config.get('name', 'TokenGovernor'),
            description=config.get('description', 'Standalone governance system for agentic coding workflows'),
            private=repo_config.get('private', False),
            auto_init=False,  # We already have local files
            default_branch=repo_config.get('default_branch', 'main')
        )
        
        print(f"✅ Created repository: {repo.html_url}")
        return repo.clone_url
    
    def setup_branch_protection(self, repo_name: str, branch: str = 'main'):
        """Set up branch protection rules"""
        repo = self.user.get_repo(repo_name)
        branch_obj = repo.get_branch(branch)
        
        # Enable branch protection
        branch_obj.edit_protection(
            strict=True,
            contexts=['ci'],  # Require CI to pass
            enforce_admins=True,
            dismiss_stale_reviews=True,
            require_code_owner_reviews=False,
            required_approving_review_count=1
        )
        
        print(f"✅ Branch protection enabled for {branch}")
    
    def get_repo_info(self, repo_name: str) -> Dict[str, Any]:
        """Get repository information"""
        repo = self.user.get_repo(repo_name)
        return {
            'name': repo.name,
            'full_name': repo.full_name,
            'html_url': repo.html_url,
            'clone_url': repo.clone_url,
            'default_branch': repo.default_branch,
            'private': repo.private
        }


def setup_github_repo():
    """Main function to set up GitHub repository"""
    # Load project configuration
    with open('project_config.json', 'r') as f:
        config = json.load(f)
    
    # Initialize GitHub manager
    manager = GitHubRepoManager()
    
    # Create repository
    clone_url = manager.create_repository(config)
    
    # Return repository information
    return {
        'clone_url': clone_url,
        'repo_name': config['repository']['name']
    }


if __name__ == "__main__":
    repo_info = setup_github_repo()
    print(f"Repository created: {repo_info['clone_url']}")