import pytest
from app.services.rules_engine import RulesEngine
from app.models.student import Student
from app.models.eligibility import EligibilityRule
import uuid

def test_rules_engine_eligible():
    """Test that a student who meets all criteria is eligible."""
    student = Student(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        college_id="TEST001",
        branch="Computer Science",
        batch=2026,
        cgpa=8.5,
        active_backlogs=0
    )
    
    rule = EligibilityRule(
        placement_drive_id=uuid.uuid4(),
        minimum_cgpa=8.0,
        maximum_active_backlogs=0,
        allowed_branches=["Computer Science", "Information Technology"]
    )
    
    engine = RulesEngine()
    result = engine.evaluate(student, rule, rule.placement_drive_id)
    
    assert result.is_eligible is True
    assert "Student satisfies all eligibility criteria." in result.reasons

def test_rules_engine_low_cgpa():
    """Test that a student with low CGPA is rejected."""
    student = Student(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        college_id="TEST002",
        branch="Computer Science",
        batch=2026,
        cgpa=7.5,
        active_backlogs=0
    )
    
    rule = EligibilityRule(
        placement_drive_id=uuid.uuid4(),
        minimum_cgpa=8.0,
        maximum_active_backlogs=0,
        allowed_branches=["Computer Science"]
    )
    
    engine = RulesEngine()
    result = engine.evaluate(student, rule, rule.placement_drive_id)
    
    assert result.is_eligible is False
    assert any("is below the minimum required CGPA" in r for r in result.reasons)

def test_rules_engine_active_backlogs():
    """Test that a student with active backlogs is rejected."""
    student = Student(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        college_id="TEST003",
        branch="Computer Science",
        batch=2026,
        cgpa=9.0,
        active_backlogs=1
    )
    
    rule = EligibilityRule(
        placement_drive_id=uuid.uuid4(),
        minimum_cgpa=8.0,
        maximum_active_backlogs=0,
        allowed_branches=["Computer Science"]
    )
    
    engine = RulesEngine()
    result = engine.evaluate(student, rule, rule.placement_drive_id)
    
    assert result.is_eligible is False
    assert any("exceed the maximum allowed" in r for r in result.reasons)

def test_rules_engine_wrong_branch():
    """Test that a student in an unallowed branch is rejected."""
    student = Student(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        college_id="TEST004",
        branch="Mechanical Engineering",
        batch=2026,
        cgpa=8.5,
        active_backlogs=0
    )
    
    rule = EligibilityRule(
        placement_drive_id=uuid.uuid4(),
        minimum_cgpa=8.0,
        maximum_active_backlogs=0,
        allowed_branches=["Computer Science", "Information Technology"]
    )
    
    engine = RulesEngine()
    result = engine.evaluate(student, rule, rule.placement_drive_id)
    
    assert result.is_eligible is False
    assert any("is not eligible. Allowed branches:" in r for r in result.reasons)
