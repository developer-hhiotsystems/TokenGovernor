"""Configuration management for TokenGovernor"""
import os
from typing import Dict, Any, Optional
from pathlib import Path
import json
from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """Database configuration"""
    type: str = "sqlite"
    path: str = "workflow_data.db"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30


class ClaudeFlowConfig(BaseModel):
    """Claude Flow configuration"""
    max_agents: int = 5
    context_window_size: int = 8192
    rate_limit_per_minute: int = 5
    retry_attempts: int = 3
    backoff_base: float = 2.0
    backoff_max: float = 60.0


class TokenConfig(BaseModel):
    """Token management configuration"""
    default_budget: int = 100000
    monitoring_interval: int = 300  # seconds
    alert_thresholds: Dict[str, float] = Field(default_factory=lambda: {
        "warning": 0.8,
        "critical": 0.95
    })
    ccusage_enabled: bool = True
    encryption_enabled: bool = True


class SchedulerConfig(BaseModel):
    """Scheduler configuration"""
    max_concurrent_tasks: int = 10
    default_rate_limit: int = 10  # tasks per minute
    queue_check_interval: int = 60  # seconds
    ml_optimization_enabled: bool = False  # Phase 3


class GitHubConfig(BaseModel):
    """GitHub integration configuration"""
    token: Optional[str] = None
    rate_limit_per_hour: int = 5000
    pr_template_path: str = ".github/pull_request_template.md"
    default_branch: str = "main"
    auto_merge_enabled: bool = False
    branch_protection_enabled: bool = True


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "logs/tokengovernor.log"
    max_file_size: str = "10MB"
    backup_count: int = 5


class Settings(BaseModel):
    """Main settings model"""
    # Environment
    environment: str = "development"
    debug: bool = False
    
    # Core configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    claude_flow: ClaudeFlowConfig = Field(default_factory=ClaudeFlowConfig)
    token_management: TokenConfig = Field(default_factory=TokenConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # Phase-specific settings
    current_phase: str = "Phase 0"
    phase_0_enabled: bool = True
    phase_1_enabled: bool = False
    phase_2_enabled: bool = False
    phase_3_enabled: bool = False
    
    # API settings
    api_host: str = "localhost"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    
    class Config:
        env_prefix = "TOKENGOVERNOR_"
        case_sensitive = False


def load_settings(config_path: Optional[Path] = None) -> Settings:
    """Load settings from environment and config file"""
    if config_path is None:
        config_path = Path("config") / "tokengovernor.json"
    
    # Start with defaults
    settings_dict = {}
    
    # Load from config file if exists
    if config_path.exists():
        with open(config_path, 'r') as f:
            file_config = json.load(f)
            settings_dict.update(file_config)
    
    # Override with environment variables
    env_overrides = {}
    
    # GitHub token from environment
    github_token = os.getenv('GITHUB_TOKEN')
    if github_token:
        if 'github' not in env_overrides:
            env_overrides['github'] = {}
        env_overrides['github']['token'] = github_token
    
    # Database path
    db_path = os.getenv('TOKENGOVERNOR_DATABASE_PATH')
    if db_path:
        if 'database' not in env_overrides:
            env_overrides['database'] = {}
        env_overrides['database']['path'] = db_path
    
    # Debug mode
    debug = os.getenv('TOKENGOVERNOR_DEBUG', '').lower() in ('true', '1', 'yes')
    if debug:
        env_overrides['debug'] = True
        if 'logging' not in env_overrides:
            env_overrides['logging'] = {}
        env_overrides['logging']['level'] = 'DEBUG'
    
    # Environment
    environment = os.getenv('TOKENGOVERNOR_ENVIRONMENT', 'development')
    env_overrides['environment'] = environment
    
    # Merge configurations
    settings_dict.update(env_overrides)
    
    return Settings(**settings_dict)


def save_settings(settings: Settings, config_path: Optional[Path] = None) -> None:
    """Save settings to config file"""
    if config_path is None:
        config_path = Path("config") / "tokengovernor.json"
    
    # Create config directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dict and save (excluding sensitive data)
    settings_dict = settings.dict()
    
    # Remove sensitive information
    if 'github' in settings_dict and 'token' in settings_dict['github']:
        settings_dict['github']['token'] = None
    
    with open(config_path, 'w') as f:
        json.dump(settings_dict, f, indent=2)


# Global settings instance
settings = load_settings()