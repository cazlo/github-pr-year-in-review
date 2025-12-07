"""Tests for the ReportGenerator class."""

import pytest
import json
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
            "title": "feat: Add feature A",
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
            "commit_messages": ["feat: add new feature"],
            "repo": "org/repo1",
        },
        {
            "number": 2,
            "title": "fix: Fix bug B",
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
            "commit_messages": ["fix: resolve bug"],
            "repo": "org/repo2",
        },
    ]


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    return tmp_path / "reports"


def test_format_time():
    """Test time formatting."""
    generator = ReportGenerator("org", "user", 2024)

    assert generator._format_time(None) == "N/A"
    assert generator._format_time(0.5) == "30m"
    assert generator._format_time(2.5) == "2h 30m"
    assert generator._format_time(25.0) == "1d 1h"
    assert generator._format_time(50.5) == "2d 2h"


def test_format_currency():
    """Test currency formatting."""
    generator = ReportGenerator("org", "user", 2024)
    
    assert generator._format_currency(1000) == "$1,000"
    assert generator._format_currency(1234567) == "$1,234,567"


def test_generate_yearly_summary_aggregated(sample_pr_data, temp_output_dir):
    """Test aggregated yearly summary generation."""
    analyzer = PRAnalyzer(sample_pr_data)
    generator = ReportGenerator("myorg", "testuser", 2024)

    output_path = temp_output_dir / "summary.md"
    generator.generate_yearly_summary_aggregated(analyzer, str(output_path))

    assert output_path.exists()
    content = output_path.read_text()

    # Check that key sections are present
    assert "# GitHub PR Year in Review - 2024 (Aggregated)" in content
    assert "Organization:** myorg" in content
    assert "User:** testuser" in content
    assert "Total PRs:** 2" in content
    assert "Merged:** 2" in content
    assert "Conventional Commits Analysis" in content
    assert "Business Value & Cost Savings" in content


def test_generate_yearly_summary_by_repo(sample_pr_data, temp_output_dir):
    """Test yearly summary by repository."""
    pr_data_by_repo = {
        "org/repo1": [sample_pr_data[0]],
        "org/repo2": [sample_pr_data[1]],
    }
    analyzer_by_repo = {
        "org/repo1": PRAnalyzer([sample_pr_data[0]]),
        "org/repo2": PRAnalyzer([sample_pr_data[1]]),
    }
    generator = ReportGenerator("myorg", "testuser", 2024)

    output_path = temp_output_dir / "by_repo_summary.md"
    generator.generate_yearly_summary_by_repo(pr_data_by_repo, analyzer_by_repo, str(output_path))

    assert output_path.exists()
    content = output_path.read_text()

    assert "# GitHub PR Year in Review - 2024 (By Repository)" in content
    assert "org/repo1" in content
    assert "org/repo2" in content
    assert "Conventional Commits" in content


def test_generate_monthly_breakdown_aggregated(sample_pr_data, temp_output_dir):
    """Test aggregated monthly breakdown generation."""
    analyzer = PRAnalyzer(sample_pr_data)
    monthly_data = analyzer.get_monthly_breakdown()
    generator = ReportGenerator("myorg", "testuser", 2024)

    output_path = temp_output_dir / "monthly.md"
    generator.generate_monthly_breakdown_aggregated(monthly_data, str(output_path))

    assert output_path.exists()
    content = output_path.read_text()

    assert "# Monthly Breakdown - 2024 (Aggregated)" in content
    assert "Organization:** myorg" in content
    assert "January 2024" in content
    assert "February 2024" in content


def test_generate_json_output(sample_pr_data, temp_output_dir):
    """Test JSON output generation."""
    pr_data_by_repo = {
        "org/repo1": [sample_pr_data[0]],
        "org/repo2": [sample_pr_data[1]],
    }
    analyzer_by_repo = {
        "org/repo1": PRAnalyzer([sample_pr_data[0]]),
        "org/repo2": PRAnalyzer([sample_pr_data[1]]),
    }
    aggregated_analyzer = PRAnalyzer(sample_pr_data)
    generator = ReportGenerator("myorg", "testuser", 2024)

    output_path = temp_output_dir / "data.json"
    generator.generate_json_output(
        pr_data_by_repo, analyzer_by_repo, aggregated_analyzer, str(output_path)
    )

    assert output_path.exists()
    
    # Load and validate JSON
    with open(output_path) as f:
        data = json.load(f)
    
    assert data["metadata"]["organization"] == "myorg"
    assert data["metadata"]["user"] == "testuser"
    assert data["metadata"]["year"] == 2024
    assert data["summary"]["total_prs"] == 2
    assert "repositories" in data
    assert "aggregated_metrics" in data


def test_reports_create_directory_if_not_exists(sample_pr_data, temp_output_dir):
    """Test that directories are created if they don't exist."""
    analyzer = PRAnalyzer(sample_pr_data)
    generator = ReportGenerator("myorg", "testuser", 2024)

    nested_path = temp_output_dir / "nested" / "path" / "summary.md"
    generator.generate_yearly_summary_aggregated(analyzer, str(nested_path))

    assert nested_path.exists()
    assert nested_path.parent.exists()
