"""Tests for the ReportGenerator class."""

import pytest
from datetime import datetime
from pathlib import Path
from github_pr_review.analyzer import PRAnalyzer
from github_pr_review.report_generator import ReportGenerator


@pytest.fixture
def sample_pr_data():
    """Sample PR data for testing."""
    return [
        {
            "number": 1,
            "title": "Add feature A",
            "state": "closed",
            "created_at": datetime(2024, 1, 15, 10, 0),
            "closed_at": datetime(2024, 1, 16, 14, 0),
            "merged_at": datetime(2024, 1, 16, 14, 0),
            "merged": True,
            "author": "user1",
            "description": "Implements #123",
            "labels": ["enhancement"],
            "time_to_close_hours": 28.0,
            "url": "https://github.com/owner/repo/pull/1",
            "additions": 100,
            "deletions": 20,
            "changed_files": 5,
        },
        {
            "number": 2,
            "title": "Fix bug B",
            "state": "closed",
            "created_at": datetime(2024, 2, 20, 9, 0),
            "closed_at": datetime(2024, 2, 20, 10, 0),
            "merged_at": datetime(2024, 2, 20, 10, 0),
            "merged": True,
            "author": "user2",
            "description": "Fixes PROJ-456",
            "labels": ["bug"],
            "time_to_close_hours": 1.0,
            "url": "https://github.com/owner/repo/pull/2",
            "additions": 50,
            "deletions": 30,
            "changed_files": 2,
        },
    ]


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    return tmp_path / "reports"


def test_format_time():
    """Test time formatting."""
    generator = ReportGenerator("owner", "repo", 2024)

    assert generator._format_time(None) == "N/A"
    assert generator._format_time(0.5) == "30m"
    assert generator._format_time(2.5) == "2h 30m"
    assert generator._format_time(25.0) == "1d 1h"
    assert generator._format_time(50.5) == "2d 2h"


def test_generate_yearly_summary(sample_pr_data, temp_output_dir):
    """Test yearly summary generation."""
    analyzer = PRAnalyzer(sample_pr_data)
    generator = ReportGenerator("owner", "repo", 2024)

    output_path = temp_output_dir / "summary.md"
    generator.generate_yearly_summary(analyzer, sample_pr_data, str(output_path))

    assert output_path.exists()
    content = output_path.read_text()

    # Check that key sections are present
    assert "# GitHub PR Year in Review - 2024" in content
    assert "Repository:** owner/repo" in content
    assert "Total PRs:** 2" in content
    assert "Merged:** 2" in content
    assert "GitHub Issues Referenced:" in content
    assert "Jira Tickets Referenced:" in content
    assert "Monthly Breakdown" in content
    assert "Top Contributors" in content


def test_generate_monthly_breakdown(sample_pr_data, temp_output_dir):
    """Test monthly breakdown generation."""
    analyzer = PRAnalyzer(sample_pr_data)
    monthly_data = analyzer.get_monthly_breakdown()
    generator = ReportGenerator("owner", "repo", 2024)

    output_path = temp_output_dir / "monthly.md"
    generator.generate_monthly_breakdown(monthly_data, str(output_path))

    assert output_path.exists()
    content = output_path.read_text()

    # Check that key sections are present
    assert "# Monthly Breakdown - 2024" in content
    assert "Repository:** owner/repo" in content
    assert "January 2024" in content
    assert "February 2024" in content
    assert "Overview" in content
    assert "Work Items" in content
    assert "Code Changes" in content


def test_generate_yearly_summary_creates_directory(sample_pr_data, temp_output_dir):
    """Test that directory is created if it doesn't exist."""
    analyzer = PRAnalyzer(sample_pr_data)
    generator = ReportGenerator("owner", "repo", 2024)

    nested_path = temp_output_dir / "nested" / "path" / "summary.md"
    generator.generate_yearly_summary(analyzer, sample_pr_data, str(nested_path))

    assert nested_path.exists()
    assert nested_path.parent.exists()


def test_generate_monthly_breakdown_creates_directory(sample_pr_data, temp_output_dir):
    """Test that directory is created if it doesn't exist."""
    analyzer = PRAnalyzer(sample_pr_data)
    monthly_data = analyzer.get_monthly_breakdown()
    generator = ReportGenerator("owner", "repo", 2024)

    nested_path = temp_output_dir / "nested" / "path" / "monthly.md"
    generator.generate_monthly_breakdown(monthly_data, str(nested_path))

    assert nested_path.exists()
    assert nested_path.parent.exists()


def test_yearly_summary_contains_statistics(sample_pr_data, temp_output_dir):
    """Test that yearly summary contains proper statistics."""
    analyzer = PRAnalyzer(sample_pr_data)
    generator = ReportGenerator("owner", "repo", 2024)

    output_path = temp_output_dir / "summary.md"
    generator.generate_yearly_summary(analyzer, sample_pr_data, str(output_path))

    content = output_path.read_text()

    # Verify specific statistics
    assert "Total PRs:** 2" in content
    assert "Merged:** 2" in content
    assert "100.0%" in content  # 100% merged
    assert "user1" in content
    assert "user2" in content
