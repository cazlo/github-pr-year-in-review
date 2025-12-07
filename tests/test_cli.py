"""Tests for the CLI module."""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from pathlib import Path
from click.testing import CliRunner

from github_pr_review.cli import main


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_pr_data():
    """Create sample PR data for testing."""
    return [
        {
            "number": 1,
            "title": "feat: add feature",
            "state": "closed",
            "created_at": "2024-01-15T10:00:00",
            "closed_at": "2024-01-16T14:00:00",
            "merged_at": "2024-01-16T14:00:00",
            "merged": True,
            "author": "testuser",
            "description": "Test description #123",
            "labels": ["enhancement"],
            "time_to_close_hours": 28.0,
            "url": "https://github.com/test-org/test-repo/pull/1",
            "additions": 100,
            "deletions": 50,
            "changed_files": 5,
            "commit_messages": ["feat: add feature", "test: add tests"],
            "repository": "test-org/test-repo"
        },
        {
            "number": 2,
            "title": "fix: bug fix",
            "state": "closed",
            "created_at": "2024-02-10T10:00:00",
            "closed_at": "2024-02-11T12:00:00",
            "merged_at": "2024-02-11T12:00:00",
            "merged": True,
            "author": "testuser",
            "description": "Test fix PROJ-456",
            "labels": ["bug"],
            "time_to_close_hours": 26.0,
            "url": "https://github.com/test-org/test-repo/pull/2",
            "additions": 50,
            "deletions": 25,
            "changed_files": 3,
            "commit_messages": ["fix: bug fix"],
            "repository": "test-org/test-repo"
        }
    ]


@pytest.fixture
def mock_github_client():
    """Create a mock GitHub client."""
    with patch("github_pr_review.cli.GitHubPRClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock repository
        mock_repo = Mock()
        mock_repo.full_name = "test-org/test-repo"
        
        # Mock PR
        mock_pr = Mock()
        mock_pr.number = 1
        mock_pr.title = "feat: add feature"
        mock_pr.state = "closed"
        mock_pr.created_at = datetime(2024, 1, 15, 10, 0)
        mock_pr.closed_at = datetime(2024, 1, 16, 14, 0)
        mock_pr.merged_at = datetime(2024, 1, 16, 14, 0)
        mock_pr.merged = True
        mock_pr.user = Mock()
        mock_pr.user.login = "testuser"
        mock_pr.body = "Test description #123"
        
        label = Mock()
        label.name = "enhancement"
        mock_pr.labels = [label]
        mock_pr.html_url = "https://github.com/test-org/test-repo/pull/1"
        mock_pr.additions = 100
        mock_pr.deletions = 50
        mock_pr.changed_files = 5
        
        # Mock commits
        mock_commit = Mock()
        mock_commit.commit.message = "feat: add feature"
        mock_pr.get_commits.return_value = [mock_commit]
        
        mock_client.get_user_repos_in_org.return_value = [mock_repo]
        mock_client.get_prs_for_user_in_repo.return_value = [mock_pr]
        mock_client.extract_pr_data.return_value = {
            "number": 1,
            "title": "feat: add feature",
            "state": "closed",
            "created_at": datetime(2024, 1, 15, 10, 0),
            "closed_at": datetime(2024, 1, 16, 14, 0),
            "merged_at": datetime(2024, 1, 16, 14, 0),
            "merged": True,
            "author": "testuser",
            "description": "Test description #123",
            "labels": ["enhancement"],
            "time_to_close_hours": 28.0,
            "url": "https://github.com/test-org/test-repo/pull/1",
            "additions": 100,
            "deletions": 50,
            "changed_files": 5,
            "commit_messages": ["feat: add feature"],
            "repository": "test-org/test-repo"
        }
        
        yield mock_client


def test_cli_missing_token_without_pr_data_file(runner):
    """Test that CLI fails when token is missing and no pr-data-file is provided."""
    result = runner.invoke(main, ["test-org", "test-user", "--year", "2024"])
    
    assert result.exit_code == 1
    assert "GitHub token is required" in result.output
    assert "--pr-data-file" in result.output


def test_cli_with_token_env_var(runner, mock_github_client, tmp_path):
    """Test CLI with token from environment variable."""
    output_dir = tmp_path / "reports"
    
    result = runner.invoke(
        main,
        ["test-org", "test-user", "--year", "2024", "--output-dir", str(output_dir)],
        env={"GITHUB_TOKEN": "test_token"}
    )
    
    assert result.exit_code == 0
    assert "Analyzing PRs" in result.output
    assert "Reports generated successfully" in result.output
    
    # Verify files were created
    assert (output_dir / "test-org-test-user-2024-raw-pr-data.json").exists()
    assert (output_dir / "test-org-test-user-2024-data.json").exists()
    assert (output_dir / "test-org-test-user-2024-by-repo-summary.md").exists()
    assert (output_dir / "test-org-test-user-2024-aggregated-summary.md").exists()
    assert (output_dir / "test-org-test-user-2024-by-repo-monthly.md").exists()
    assert (output_dir / "test-org-test-user-2024-aggregated-monthly.md").exists()


def test_cli_with_token_flag(runner, mock_github_client, tmp_path):
    """Test CLI with token from command-line flag."""
    output_dir = tmp_path / "reports"
    
    result = runner.invoke(
        main,
        [
            "test-org",
            "test-user",
            "--year", "2024",
            "--token", "test_token",
            "--output-dir", str(output_dir)
        ]
    )
    
    assert result.exit_code == 0
    assert "Reports generated successfully" in result.output


def test_cli_with_pr_data_file(runner, sample_pr_data, tmp_path):
    """Test CLI loading data from pr-data-file (no token required)."""
    # Create a temp pr-data file
    pr_data_file = tmp_path / "pr-data.json"
    with open(pr_data_file, 'w') as f:
        json.dump(sample_pr_data, f)
    
    output_dir = tmp_path / "reports"
    
    result = runner.invoke(
        main,
        [
            "test-org",
            "test-user",
            "--year", "2024",
            "--output-dir", str(output_dir),
            "--pr-data-file", str(pr_data_file)
        ]
    )
    
    assert result.exit_code == 0
    assert "Loading PR data from" in result.output
    assert "Loaded 2 pull requests" in result.output
    assert "Reports generated successfully" in result.output
    
    # Verify reports were created (but not raw-pr-data since we loaded from file)
    assert (output_dir / "test-org-test-user-2024-data.json").exists()
    assert (output_dir / "test-org-test-user-2024-by-repo-summary.md").exists()


def test_cli_pr_data_file_not_found(runner, tmp_path):
    """Test CLI with non-existent pr-data-file."""
    result = runner.invoke(
        main,
        [
            "test-org",
            "test-user",
            "--year", "2024",
            "--pr-data-file", str(tmp_path / "nonexistent.json")
        ]
    )
    
    assert result.exit_code == 1
    assert "File not found" in result.output


def test_cli_no_repos_found(runner, tmp_path):
    """Test CLI when no repositories are found."""
    with patch("github_pr_review.cli.GitHubPRClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_user_repos_in_org.return_value = []
        
        output_dir = tmp_path / "reports"
        
        result = runner.invoke(
            main,
            [
                "test-org",
                "test-user",
                "--year", "2024",
                "--token", "test_token",
                "--output-dir", str(output_dir)
            ]
        )
        
        assert result.exit_code == 0
        assert "No repositories found" in result.output


def test_cli_no_prs_found(runner, tmp_path):
    """Test CLI when no PRs are found."""
    with patch("github_pr_review.cli.GitHubPRClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_repo = Mock()
        mock_repo.full_name = "test-org/test-repo"
        
        mock_client.get_user_repos_in_org.return_value = [mock_repo]
        mock_client.get_prs_for_user_in_repo.return_value = []
        
        output_dir = tmp_path / "reports"
        
        result = runner.invoke(
            main,
            [
                "test-org",
                "test-user",
                "--year", "2024",
                "--token", "test_token",
                "--output-dir", str(output_dir)
            ]
        )
        
        assert result.exit_code == 0
        assert "No pull requests found" in result.output


def test_cli_default_year(runner, mock_github_client, tmp_path):
    """Test CLI uses current year when year is not specified."""
    output_dir = tmp_path / "reports"
    current_year = datetime.now().year
    
    result = runner.invoke(
        main,
        [
            "test-org",
            "test-user",
            "--token", "test_token",
            "--output-dir", str(output_dir)
        ]
    )
    
    assert result.exit_code == 0
    assert f"Year: {current_year}" in result.output


def test_cli_creates_output_directory(runner, mock_github_client, tmp_path):
    """Test that CLI creates output directory if it doesn't exist."""
    output_dir = tmp_path / "new_reports" / "nested"
    
    result = runner.invoke(
        main,
        [
            "test-org",
            "test-user",
            "--year", "2024",
            "--token", "test_token",
            "--output-dir", str(output_dir)
        ]
    )
    
    assert result.exit_code == 0
    assert output_dir.exists()


def test_cli_summary_statistics(runner, mock_github_client, tmp_path):
    """Test that CLI displays summary statistics."""
    output_dir = tmp_path / "reports"
    
    result = runner.invoke(
        main,
        [
            "test-org",
            "test-user",
            "--year", "2024",
            "--token", "test_token",
            "--output-dir", str(output_dir)
        ]
    )
    
    assert result.exit_code == 0
    assert "Summary:" in result.output
    assert "Total PRs:" in result.output
    assert "Merged:" in result.output
    assert "Repositories:" in result.output
    assert "Estimated Cost Savings:" in result.output


def test_cli_exception_handling(runner, tmp_path):
    """Test that CLI handles exceptions gracefully."""
    with patch("github_pr_review.cli.GitHubPRClient") as mock_client_class:
        mock_client_class.side_effect = Exception("API Error")
        
        output_dir = tmp_path / "reports"
        
        result = runner.invoke(
            main,
            [
                "test-org",
                "test-user",
                "--year", "2024",
                "--token", "test_token",
                "--output-dir", str(output_dir)
            ]
        )
        
        assert result.exit_code == 1
        assert "Error:" in result.output


def test_cli_datetime_parsing_from_json(runner, tmp_path):
    """Test that datetime strings are correctly parsed when loading from JSON."""
    pr_data = [
        {
            "number": 1,
            "title": "test",
            "state": "closed",
            "created_at": "2024-01-15T10:00:00+00:00",
            "closed_at": "2024-01-16T14:00:00+00:00",
            "merged_at": "2024-01-16T14:00:00+00:00",
            "merged": True,
            "author": "testuser",
            "description": "Test",
            "labels": [],
            "time_to_close_hours": 28.0,
            "url": "https://github.com/test-org/test-repo/pull/1",
            "additions": 100,
            "deletions": 50,
            "changed_files": 5,
            "commit_messages": ["test"],
            "repository": "test-org/test-repo"
        }
    ]
    
    pr_data_file = tmp_path / "pr-data.json"
    with open(pr_data_file, 'w') as f:
        json.dump(pr_data, f)
    
    output_dir = tmp_path / "reports"
    
    result = runner.invoke(
        main,
        [
            "test-org",
            "test-user",
            "--year", "2024",
            "--output-dir", str(output_dir),
            "--pr-data-file", str(pr_data_file)
        ]
    )
    
    assert result.exit_code == 0
    assert "Reports generated successfully" in result.output


def test_cli_multiple_repositories(runner, sample_pr_data, tmp_path):
    """Test CLI with PRs from multiple repositories."""
    # Add PRs from another repo
    pr_data = sample_pr_data.copy()
    pr_data.append({
        "number": 3,
        "title": "docs: update docs",
        "state": "closed",
        "created_at": "2024-03-01T10:00:00",
        "closed_at": "2024-03-01T12:00:00",
        "merged_at": "2024-03-01T12:00:00",
        "merged": True,
        "author": "testuser",
        "description": "Update documentation",
        "labels": ["documentation"],
        "time_to_close_hours": 2.0,
        "url": "https://github.com/test-org/another-repo/pull/3",
        "additions": 20,
        "deletions": 5,
        "changed_files": 1,
        "commit_messages": ["docs: update docs"],
        "repository": "test-org/another-repo"
    })
    
    pr_data_file = tmp_path / "pr-data.json"
    with open(pr_data_file, 'w') as f:
        json.dump(pr_data, f)
    
    output_dir = tmp_path / "reports"
    
    result = runner.invoke(
        main,
        [
            "test-org",
            "test-user",
            "--year", "2024",
            "--output-dir", str(output_dir),
            "--pr-data-file", str(pr_data_file)
        ]
    )
    
    assert result.exit_code == 0
    assert "Loaded 3 pull requests across 2 repositories" in result.output


def test_cli_raw_pr_data_serialization(runner, mock_github_client, tmp_path):
    """Test that raw PR data is properly serialized to JSON."""
    output_dir = tmp_path / "reports"
    
    result = runner.invoke(
        main,
        [
            "test-org",
            "test-user",
            "--year", "2024",
            "--token", "test_token",
            "--output-dir", str(output_dir)
        ]
    )
    
    assert result.exit_code == 0
    
    # Verify raw PR data file exists and is valid JSON
    raw_data_file = output_dir / "test-org-test-user-2024-raw-pr-data.json"
    assert raw_data_file.exists()
    
    with open(raw_data_file, 'r') as f:
        data = json.load(f)
        assert isinstance(data, list)
        assert len(data) > 0
        assert "repository" in data[0]


def test_cli_help(runner):
    """Test CLI help output."""
    result = runner.invoke(main, ["--help"])
    
    assert result.exit_code == 0
    assert "ORGANIZATION" in result.output
    assert "USER" in result.output
    assert "--year" in result.output
    assert "--token" in result.output
    assert "--output-dir" in result.output
    assert "--pr-data-file" in result.output

