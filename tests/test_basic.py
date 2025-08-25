"""Basic tests for TokenGovernor system"""
import pytest
from src.tokengovernor.core.models import Project, PriorityTier


def test_project_creation():
    """Test basic project creation"""
    project = Project(
        name="Test Project",
        description="A test project",
        token_budget=10000,
        priority_tier=PriorityTier.TIER_1,
        owner="test@example.com"
    )
    
    assert project.name == "Test Project"
    assert project.token_budget == 10000
    assert project.priority_tier == PriorityTier.TIER_1
    assert project.owner == "test@example.com"


def test_project_id_generation():
    """Test that project ID is automatically generated"""
    project = Project(
        name="Test Project",
        token_budget=5000,
        priority_tier=PriorityTier.TIER_2,
        owner="test@example.com"
    )
    
    assert project.project_id is not None
    assert len(project.project_id) > 0


def test_priority_tier_enum():
    """Test priority tier enumeration"""
    assert PriorityTier.TIER_1.value == "tier_1"
    assert PriorityTier.TIER_2.value == "tier_2"


if __name__ == "__main__":
    pytest.main([__file__])