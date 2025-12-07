"""GitHub API client for fetching PR data."""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from github import Github, PullRequest, Repository
from github.GithubException import GithubException


class GitHubPRClient:
    """Client for fetching and processing GitHub pull request data."""

    def __init__(self, token: str):
        """
        Initialize the GitHub client.

        Args:
            token: GitHub personal access token (required for org access).
        """
        self.github = Github(token)
        self.user = self.github.get_user()

    def get_user_repos_in_org(
        self, org_name: str, username: str
    ) -> List[Repository.Repository]:
        """
        Get all repositories in an organization where a user has contributed.

        Args:
            org_name: Organization name
            username: GitHub username

        Returns:
            List of Repository objects
        """
        try:
            org = self.github.get_organization(org_name)
            repos = []
            
            # Get all repos in the org (includes private if token has access)
            for repo in org.get_repos(type="all"):
                # Check if user has contributed to this repo
                try:
                    # Try to get at least one PR or commit from user
                    repo_prs = repo.get_pulls(state="all")
                    for pr in repo_prs:
                        if pr.user and pr.user.login == username:
                            repos.append(repo)
                            break
                except GithubException:
                    # Skip repos we can't access
                    continue
            
            return repos
        except GithubException as e:
            raise RuntimeError(f"Failed to fetch repos for org {org_name}: {e}")

    def get_prs_for_user_in_repo(
        self, repo: Repository.Repository, username: str, year: Optional[int] = None
    ) -> List[PullRequest.PullRequest]:
        """
        Fetch all pull requests by a specific user in a repository for a given year.

        Args:
            repo: Repository object
            username: GitHub username
            year: Year to fetch PRs for. If None, uses the last 365 days from now.

        Returns:
            List of PullRequest objects
        """
        # Calculate date range
        if year:
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31, 23, 59, 59)
        else:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)

        prs = []
        try:
            # Get all PRs by this user (both open and closed)
            for state in ["closed", "open"]:
                state_prs = repo.get_pulls(state=state, sort="created", direction="desc")
                for pr in state_prs:
                    if pr.created_at < start_date:
                        break
                    if pr.user and pr.user.login == username and start_date <= pr.created_at <= end_date:
                        prs.append(pr)
        except GithubException as e:
            # Skip repos where we can't fetch PRs
            pass

        return prs

    def get_prs_for_year(
        self, owner: str, repo: str, year: Optional[int] = None
    ) -> List[PullRequest.PullRequest]:
        """
        Fetch all pull requests for a given year (legacy method for single repo).

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
            # Get closed PRs within date range (sort by created for proper date filtering)
            closed_prs = repository.get_pulls(state="closed", sort="created", direction="desc")
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

    def extract_pr_data(self, pr: PullRequest.PullRequest, repo_name: str = None) -> Dict[str, Any]:
        """
        Extract relevant data from a pull request.

        Args:
            pr: PullRequest object
            repo_name: Repository name (optional, for org-wide analysis)

        Returns:
            Dictionary containing PR data
        """
        # Calculate time to close
        time_to_close = None
        if pr.closed_at and pr.created_at:
            time_to_close = (pr.closed_at - pr.created_at).total_seconds() / 3600  # hours

        # Get commit messages for conventional commit analysis
        commit_messages = []
        try:
            for commit in pr.get_commits():
                if commit.commit and commit.commit.message:
                    commit_messages.append(commit.commit.message)
        except:
            pass

        data = {
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
            "commit_messages": commit_messages,
        }
        
        if repo_name:
            data["repo"] = repo_name
            
        return data
