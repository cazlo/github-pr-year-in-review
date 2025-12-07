"""Tests for the GitHubPRClient class."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from github.GithubException import GithubException
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
    """Test client initialization without token - now requires token."""
    with patch("github_pr_review.github_client.Github") as mock_github:
        # Token is now required
        client = GitHubPRClient("test_token")
        mock_github.assert_called_once_with("test_token")


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
    mock_pr1.created_at = datetime(2024, 6, 15, tzinfo=timezone.utc)

    mock_pr2 = Mock()
    mock_pr2.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)

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


@patch("github_pr_review.github_client.Github")
def test_get_user_repos_in_org_org_success(mock_github_class):
    """Include repos when target user has authored PRs in the org."""
    mock_github = Mock()
    mock_github_class.return_value = mock_github

    mock_org = Mock()
    mock_github.get_organization.return_value = mock_org

    repo_matching = Mock()
    repo_matching.full_name = "org/repo"
    pr = Mock()
    pr.user = Mock()
    pr.user.login = "target"
    repo_matching.get_pulls.return_value = [pr]

    repo_duplicate = Mock()
    repo_duplicate.full_name = "org/repo"
    repo_duplicate.get_pulls.return_value = [Mock()]

    repo_no_pr = Mock()
    repo_no_pr.full_name = "org/other"
    pr2 = Mock()
    pr2.user = Mock()
    pr2.user.login = "other"
    repo_no_pr.get_pulls.return_value = [pr2]

    mock_org.get_repos.return_value = [repo_matching, repo_duplicate, repo_no_pr]

    client = GitHubPRClient("token")
    repos = client.get_user_repos_in_org("org", "target")

    assert repos == [repo_matching]


@patch("github_pr_review.github_client.Github")
def test_get_user_repos_in_org_fallback_to_user(mock_github_class):
    """Fall back to the authenticated user's repos when org lookup fails."""
    mock_github = Mock()
    mock_github_class.return_value = mock_github

    mock_github.get_organization.side_effect = GithubException(404, "org not found", None)
    mock_user = Mock()
    mock_github.get_user.return_value = mock_user

    repo_via_user = Mock()
    repo_via_user.full_name = "user/repo"
    pr = Mock()
    pr.user = Mock()
    pr.user.login = "target-user"
    repo_via_user.get_pulls.return_value = [pr]
    mock_user.get_repos.return_value = [repo_via_user]

    client = GitHubPRClient("token")
    repos = client.get_user_repos_in_org("org", "target-user")

    assert repos == [repo_via_user]


@patch("github_pr_review.github_client.Github")
def test_get_user_repos_in_org_skip_inaccessible(mock_github_class):
    """When a repo cannot be accessed, it should be skipped."""
    mock_github = Mock()
    mock_github_class.return_value = mock_github

    mock_org = Mock()
    mock_github.get_organization.return_value = mock_org

    repo = Mock()
    repo.full_name = "org/repo"
    repo.get_pulls.side_effect = GithubException(403, "no access", None)
    mock_org.get_repos.return_value = [repo]

    client = GitHubPRClient("token")
    repos = client.get_user_repos_in_org("org", "target")

    assert repos == []


def test_get_prs_for_user_in_repo_year_range():
    """Filter PRs by year and include only matching user."""
    repo = Mock()

    target = "tester"
    pr_closed = Mock()
    pr_closed.created_at = datetime(2023, 6, 1, tzinfo=timezone.utc)
    pr_closed.user = Mock()
    pr_closed.user.login = target

    pr_early = Mock()
    pr_early.created_at = datetime(2022, 12, 31, tzinfo=timezone.utc)
    pr_early.user = Mock()
    pr_early.user.login = target

    pr_open = Mock()
    pr_open.created_at = datetime(2023, 11, 1, tzinfo=timezone.utc)
    pr_open.user = Mock()
    pr_open.user.login = target

    def pulls_side_effect(state, sort, direction):
        if state == "closed":
            return [pr_closed, pr_early]
        return [pr_open]

    repo.get_pulls.side_effect = pulls_side_effect

    client = GitHubPRClient("token")
    prs = client.get_prs_for_user_in_repo(repo, target, 2023)

    assert pr_closed in prs
    assert pr_open in prs
    assert pr_early not in prs


def test_get_prs_for_user_in_repo_default_range():
    """Use last 365 days when year is not provided."""
    repo = Mock()
    repo.get_pulls.return_value = []

    client = GitHubPRClient("token")
    real_datetime = datetime

    with patch("github_pr_review.github_client.datetime", wraps=real_datetime) as mock_datetime:
        mock_datetime.now.return_value = real_datetime(2025, 1, 1, tzinfo=timezone.utc)
        prs = client.get_prs_for_user_in_repo(repo, "user", None)

    assert prs == []


@patch("github_pr_review.github_client.Github")
def test_get_prs_for_year_raises_runtime_error(mock_github_class):
    mock_github = Mock()
    mock_github_class.return_value = mock_github

    mock_repo = Mock()
    mock_repo.get_pulls.side_effect = GithubException(500, "error", None)
    mock_github.get_repo.return_value = mock_repo

    client = GitHubPRClient("token")

    with pytest.raises(RuntimeError):
        client.get_prs_for_year("owner", "repo", 2024)


def test_extract_pr_data_commits_and_repo_name(mock_pr):
    """Ensure commit messages and provided repo name are captured."""
    commit = Mock()
    commit.commit = Mock()
    commit.commit.message = "feat: add tests"
    mock_pr.get_commits.return_value = [commit]

    client = GitHubPRClient("token")
    data = client.extract_pr_data(mock_pr, repo_name="demo/repo")

    assert data["commit_messages"] == ["feat: add tests"]
    assert data["repo"] == "demo/repo"


def test_extract_pr_data_handles_commit_errors(mock_pr):
    """If commits cannot be read, result should still return empty list."""
    mock_pr.get_commits.side_effect = Exception("boom")

    client = GitHubPRClient("token")
    data = client.extract_pr_data(mock_pr)

    assert data["commit_messages"] == []
