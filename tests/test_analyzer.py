"""Tests for the PRAnalyzer class."""

import pytest
from datetime import datetime
from github_pr_review.analyzer import PRAnalyzer


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
            "description": "Implements #123 for feature A",
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
            "created_at": datetime(2024, 1, 20, 9, 0),
            "closed_at": datetime(2024, 1, 20, 10, 0),
            "merged_at": datetime(2024, 1, 20, 10, 0),
            "merged": True,
            "author": "user2",
            "description": "Fixes PROJ-456 from Jira https://example.atlassian.net/browse/PROJ-456",
            "labels": ["bug"],
            "time_to_close_hours": 1.0,
            "url": "https://github.com/owner/repo/pull/2",
            "additions": 50,
            "deletions": 30,
            "changed_files": 2,
        },
        {
            "number": 3,
            "title": "Update docs",
            "state": "closed",
            "created_at": datetime(2024, 2, 5, 14, 0),
            "closed_at": datetime(2024, 2, 5, 15, 30),
            "merged_at": None,
            "merged": False,
            "author": "user1",
            "description": "Documentation update",
            "labels": ["documentation"],
            "time_to_close_hours": 1.5,
            "url": "https://github.com/owner/repo/pull/3",
            "additions": 10,
            "deletions": 5,
            "changed_files": 1,
        },
        {
            "number": 4,
            "title": "WIP: New feature",
            "state": "open",
            "created_at": datetime(2024, 3, 1, 10, 0),
            "closed_at": None,
            "merged_at": None,
            "merged": False,
            "author": "user3",
            "description": "Work in progress for github.com/owner/repo/issues/789",
            "labels": ["wip"],
            "time_to_close_hours": None,
            "url": "https://github.com/owner/repo/pull/4",
            "additions": 200,
            "deletions": 50,
            "changed_files": 10,
        },
    ]


def test_get_total_prs(sample_pr_data):
    """Test getting total PR count."""
    analyzer = PRAnalyzer(sample_pr_data)
    assert analyzer.get_total_prs() == 4


def test_get_merged_prs_count(sample_pr_data):
    """Test getting merged PR count."""
    analyzer = PRAnalyzer(sample_pr_data)
    assert analyzer.get_merged_prs_count() == 2


def test_get_closed_prs_count(sample_pr_data):
    """Test getting closed (not merged) PR count."""
    analyzer = PRAnalyzer(sample_pr_data)
    assert analyzer.get_closed_prs_count() == 1


def test_get_open_prs_count(sample_pr_data):
    """Test getting open PR count."""
    analyzer = PRAnalyzer(sample_pr_data)
    assert analyzer.get_open_prs_count() == 1


def test_get_average_time_to_close(sample_pr_data):
    """Test calculating average time to close."""
    analyzer = PRAnalyzer(sample_pr_data)
    avg_time = analyzer.get_average_time_to_close()
    # (28.0 + 1.0 + 1.5) / 3 = 10.166...
    assert avg_time is not None
    assert 10.0 < avg_time < 10.5


def test_get_median_time_to_close(sample_pr_data):
    """Test calculating median time to close."""
    analyzer = PRAnalyzer(sample_pr_data)
    median_time = analyzer.get_median_time_to_close()
    assert median_time == 1.5  # Middle value of [1.0, 1.5, 28.0]


def test_get_prs_per_month(sample_pr_data):
    """Test grouping PRs by month."""
    analyzer = PRAnalyzer(sample_pr_data)
    prs_per_month = analyzer.get_prs_per_month()
    assert prs_per_month["2024-01"] == 2
    assert prs_per_month["2024-02"] == 1
    assert prs_per_month["2024-03"] == 1


def test_get_prs_by_author(sample_pr_data):
    """Test counting PRs by author."""
    analyzer = PRAnalyzer(sample_pr_data)
    prs_by_author = analyzer.get_prs_by_author()
    assert prs_by_author["user1"] == 2
    assert prs_by_author["user2"] == 1
    assert prs_by_author["user3"] == 1


def test_extract_work_items_github_issue():
    """Test extracting GitHub issue references."""
    analyzer = PRAnalyzer([])
    description = "This fixes #123 and resolves #456"
    work_items = analyzer.extract_work_items(description)
    assert "123" in work_items["github_issues"]
    assert "456" in work_items["github_issues"]


def test_extract_work_items_github_url():
    """Test extracting GitHub issue URLs."""
    analyzer = PRAnalyzer([])
    description = "See https://github.com/owner/repo/issues/789"
    work_items = analyzer.extract_work_items(description)
    assert "789" in work_items["github_issues"]


def test_extract_work_items_jira():
    """Test extracting Jira ticket references."""
    analyzer = PRAnalyzer([])
    description = "Implements PROJ-123 and TASK-456"
    work_items = analyzer.extract_work_items(description)
    assert "PROJ-123" in work_items["jira_tickets"]
    assert "TASK-456" in work_items["jira_tickets"]


def test_extract_work_items_jira_url():
    """Test extracting Jira ticket URLs."""
    analyzer = PRAnalyzer([])
    description = "See https://company.atlassian.net/browse/ABC-999"
    work_items = analyzer.extract_work_items(description)
    assert "ABC-999" in work_items["jira_tickets"]


def test_get_work_item_analysis(sample_pr_data):
    """Test work item analysis."""
    analyzer = PRAnalyzer(sample_pr_data)
    work_items = analyzer.get_work_item_analysis()
    assert work_items["total_github_issues"] == 2  # #123 and #789
    assert work_items["total_jira_tickets"] == 1  # PROJ-456
    assert work_items["prs_with_work_items"] == 3
    assert work_items["prs_without_work_items"] == 1
    assert work_items["percentage_with_work_items"] == 75.0


def test_get_code_change_stats(sample_pr_data):
    """Test code change statistics."""
    analyzer = PRAnalyzer(sample_pr_data)
    stats = analyzer.get_code_change_stats()
    assert stats["total_additions"] == 360  # 100 + 50 + 10 + 200
    assert stats["total_deletions"] == 105  # 20 + 30 + 5 + 50
    assert stats["total_files_changed"] == 18  # 5 + 2 + 1 + 10
    assert stats["avg_additions_per_pr"] == 90.0
    assert stats["avg_deletions_per_pr"] == 26.25
    assert stats["avg_files_per_pr"] == 4.5


def test_get_monthly_breakdown(sample_pr_data):
    """Test monthly breakdown generation."""
    analyzer = PRAnalyzer(sample_pr_data)
    monthly = analyzer.get_monthly_breakdown()
    assert "2024-01" in monthly
    assert "2024-02" in monthly
    assert "2024-03" in monthly
    assert monthly["2024-01"]["total_prs"] == 2
    assert monthly["2024-02"]["total_prs"] == 1
    assert monthly["2024-03"]["total_prs"] == 1


def test_empty_pr_list():
    """Test analyzer with empty PR list."""
    analyzer = PRAnalyzer([])
    assert analyzer.get_total_prs() == 0
    assert analyzer.get_merged_prs_count() == 0
    assert analyzer.get_average_time_to_close() is None
    assert analyzer.get_prs_per_month() == {}
