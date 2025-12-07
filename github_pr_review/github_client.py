"""GitHub API client for fetching PR data."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from github import Github, PullRequest
from github.GithubException import GithubException


class GitHubPRClient:
    """Client for fetching and processing GitHub pull request data."""

    def __init__(self, token: Optional[str] = None):
        """
        Initialize the GitHub client.

        Args:
            token: GitHub personal access token. If None, uses unauthenticated access.
        """
        self.github = Github(token) if token else Github()

    def get_prs_for_year(
        self, owner: str, repo: str, year: Optional[int] = None
    ) -> List[PullRequest.PullRequest]:
        """
        Fetch all pull requests for a given year.

        Args:
            owner: Repository owner
            repo: Repository name
            year: Year to fetch PRs for. If None, uses the last 365 days from now.

        Returns:
            List of PullRequest objects
        """
        repository = self.github.get_repo(f"{owner}/{repo}")

        # Calculate date range
        if year:
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31, 23, 59, 59)
        else:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)

        # Fetch all PRs (open and closed)
        prs = []
        try:
            # Get closed PRs within date range
            closed_prs = repository.get_pulls(state="closed", sort="updated", direction="desc")
            for pr in closed_prs:
                if pr.created_at < start_date:
                    break
                if start_date <= pr.created_at <= end_date:
                    prs.append(pr)

            # Get open PRs within date range
            open_prs = repository.get_pulls(state="open", sort="created", direction="desc")
            for pr in open_prs:
                if pr.created_at < start_date:
                    break
                if start_date <= pr.created_at <= end_date:
                    prs.append(pr)

        except GithubException as e:
            raise RuntimeError(f"Failed to fetch PRs: {e}")

        return prs

    def extract_pr_data(self, pr: PullRequest.PullRequest) -> Dict[str, Any]:
        """
        Extract relevant data from a pull request.

        Args:
            pr: PullRequest object

        Returns:
            Dictionary containing PR data
        """
        # Calculate time to close
        time_to_close = None
        if pr.closed_at and pr.created_at:
            time_to_close = (pr.closed_at - pr.created_at).total_seconds() / 3600  # hours

        return {
            "number": pr.number,
            "title": pr.title,
            "state": pr.state,
            "created_at": pr.created_at,
            "closed_at": pr.closed_at,
            "merged_at": pr.merged_at,
            "merged": pr.merged,
            "author": pr.user.login if pr.user else None,
            "description": pr.body or "",
            "labels": [label.name for label in pr.labels],
            "time_to_close_hours": time_to_close,
            "url": pr.html_url,
            "additions": pr.additions,
            "deletions": pr.deletions,
            "changed_files": pr.changed_files,
        }
