"""Test configuration management"""
import pytest
from src.tokengovernor.core.config import Settings, DatabaseConfig, ClaudeFlowConfig


def test_default_settings():
    """Test default settings configuration"""
    settings = Settings()
    
    assert settings.environment == "development"
    assert settings.debug == False
    assert settings.current_phase == "Phase 0"
    assert settings.api_host == "localhost"
    assert settings.api_port == 8000


def test_database_config():
    """Test database configuration"""
    db_config = DatabaseConfig()
    
    assert db_config.type == "sqlite"
    assert db_config.path == "workflow_data.db"
    assert db_config.pool_size == 10


def test_claude_flow_config():
    """Test Claude Flow configuration"""
    cf_config = ClaudeFlowConfig()
    
    assert cf_config.max_agents == 5
    assert cf_config.context_window_size == 8192
    assert cf_config.rate_limit_per_minute == 5
    assert cf_config.retry_attempts == 3


if __name__ == "__main__":
    pytest.main([__file__])