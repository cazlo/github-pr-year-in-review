"""Tests for the GitHubPRClient class."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from github_pr_review.github_client import GitHubPRClient


@pytest.fixture
def mock_pr():
    """Create a mock PullRequest object."""
    pr = Mock()
    pr.number = 123
    pr.title = "Test PR"
    pr.state = "closed"
    pr.created_at = datetime(2024, 1, 15, 10, 0)
    pr.closed_at = datetime(2024, 1, 16, 14, 0)
    pr.merged_at = datetime(2024, 1, 16, 14, 0)
    pr.merged = True
    pr.user = Mock()
    pr.user.login = "testuser"
    pr.body = "Test description with #123"
    # Create label mocks with name attributes
    label1 = Mock()
    label1.name = "bug"
    label2 = Mock()
    label2.name = "enhancement"
    pr.labels = [label1, label2]
    pr.html_url = "https://github.com/owner/repo/pull/123"
    pr.additions = 100
    pr.deletions = 50
    pr.changed_files = 5
    return pr


def test_client_initialization_with_token():
    """Test client initialization with token."""
    with patch("github_pr_review.github_client.Github") as mock_github:
        client = GitHubPRClient("test_token")
        mock_github.assert_called_once_with("test_token")


def test_client_initialization_without_token():
    """Test client initialization without token."""
    with patch("github_pr_review.github_client.Github") as mock_github:
        client = GitHubPRClient(None)
        mock_github.assert_called_once_with()


def test_extract_pr_data(mock_pr):
    """Test PR data extraction."""
    client = GitHubPRClient(None)
    data = client.extract_pr_data(mock_pr)

    assert data["number"] == 123
    assert data["title"] == "Test PR"
    assert data["state"] == "closed"
    assert data["merged"] is True
    assert data["author"] == "testuser"
    assert data["description"] == "Test description with #123"
    assert "bug" in data["labels"]
    assert "enhancement" in data["labels"]
    assert data["additions"] == 100
    assert data["deletions"] == 50
    assert data["changed_files"] == 5
    assert data["time_to_close_hours"] == 28.0  # 28 hours between created and closed


def test_extract_pr_data_open_pr():
    """Test PR data extraction for open PR."""
    pr = Mock()
    pr.number = 456
    pr.title = "Open PR"
    pr.state = "open"
    pr.created_at = datetime(2024, 1, 15, 10, 0)
    pr.closed_at = None
    pr.merged_at = None
    pr.merged = False
    pr.user = Mock()
    pr.user.login = "user2"
    pr.body = None
    pr.labels = []
    pr.html_url = "https://github.com/owner/repo/pull/456"
    pr.additions = 20
    pr.deletions = 10
    pr.changed_files = 2

    client = GitHubPRClient(None)
    data = client.extract_pr_data(pr)

    assert data["state"] == "open"
    assert data["merged"] is False
    assert data["closed_at"] is None
    assert data["merged_at"] is None
    assert data["time_to_close_hours"] is None
    assert data["description"] == ""


def test_extract_pr_data_no_user():
    """Test PR data extraction when user is None."""
    pr = Mock()
    pr.number = 789
    pr.title = "No user PR"
    pr.state = "closed"
    pr.created_at = datetime(2024, 1, 15, 10, 0)
    pr.closed_at = datetime(2024, 1, 15, 11, 0)
    pr.merged_at = None
    pr.merged = False
    pr.user = None
    pr.body = "Test"
    pr.labels = []
    pr.html_url = "https://github.com/owner/repo/pull/789"
    pr.additions = 5
    pr.deletions = 3
    pr.changed_files = 1

    client = GitHubPRClient(None)
    data = client.extract_pr_data(pr)

    assert data["author"] is None


@patch("github_pr_review.github_client.Github")
def test_get_prs_for_year_with_year(mock_github_class):
    """Test fetching PRs for a specific year."""
    # Setup mock
    mock_github = Mock()
    mock_github_class.return_value = mock_github

    mock_repo = Mock()
    mock_github.get_repo.return_value = mock_repo

    mock_pr1 = Mock()
    mock_pr1.created_at = datetime(2024, 6, 15)

    mock_pr2 = Mock()
    mock_pr2.created_at = datetime(2024, 1, 1)

    # Mock closed PRs
    mock_closed_prs = Mock()
    mock_closed_prs.__iter__ = Mock(return_value=iter([mock_pr1]))
    mock_repo.get_pulls.return_value = mock_closed_prs

    client = GitHubPRClient("test_token")

    # Mock the open PRs call to return empty
    def get_pulls_side_effect(state, sort, direction):
        if state == "closed":
            return iter([mock_pr1])
        else:
            return iter([mock_pr2])

    mock_repo.get_pulls.side_effect = get_pulls_side_effect

    prs = client.get_prs_for_year("owner", "repo", 2024)

    # Verify the repo was accessed correctly
    mock_github.get_repo.assert_called_once_with("owner/repo")


@patch("github_pr_review.github_client.Github")
def test_get_prs_for_year_without_year(mock_github_class):
    """Test fetching PRs for last 365 days."""
    # Setup mock
    mock_github = Mock()
    mock_github_class.return_value = mock_github

    mock_repo = Mock()
    mock_github.get_repo.return_value = mock_repo

    # Mock empty results
    mock_repo.get_pulls.return_value = iter([])

    client = GitHubPRClient("test_token")
    prs = client.get_prs_for_year("owner", "repo", None)

    # Should still call the repo
    mock_github.get_repo.assert_called_once_with("owner/repo")
