"""Analyzer for PR data to extract insights and metrics."""

import re
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any, Optional
from statistics import mean, median


class PRAnalyzer:
    """Analyzer for pull request data."""

    # Patterns for work item links
    GITHUB_ISSUE_PATTERN = re.compile(r"#(\d+)")
    GITHUB_ISSUE_URL_PATTERN = re.compile(r"github\.com/[\w-]+/[\w-]+/issues/(\d+)")
    JIRA_PATTERN = re.compile(r"([A-Z]+-\d+)")
    JIRA_URL_PATTERN = re.compile(r"[a-zA-Z0-9.-]+\.atlassian\.net/browse/([A-Z]+-\d+)")

    def __init__(self, pr_data: List[Dict[str, Any]]):
        """
        Initialize the analyzer with PR data.

        Args:
            pr_data: List of dictionaries containing PR data
        """
        self.pr_data = pr_data

    def get_total_prs(self) -> int:
        """Get total number of PRs."""
        return len(self.pr_data)

    def get_merged_prs_count(self) -> int:
        """Get count of merged PRs."""
        return sum(1 for pr in self.pr_data if pr["merged"])

    def get_closed_prs_count(self) -> int:
        """Get count of closed (but not merged) PRs."""
        return sum(1 for pr in self.pr_data if pr["state"] == "closed" and not pr["merged"])

    def get_open_prs_count(self) -> int:
        """Get count of still-open PRs."""
        return sum(1 for pr in self.pr_data if pr["state"] == "open")

    def get_average_time_to_close(self) -> Optional[float]:
        """
        Get average time to close PRs in hours.

        Returns:
            Average time in hours, or None if no closed PRs
        """
        times = [pr["time_to_close_hours"] for pr in self.pr_data if pr["time_to_close_hours"]]
        return mean(times) if times else None

    def get_median_time_to_close(self) -> Optional[float]:
        """
        Get median time to close PRs in hours.

        Returns:
            Median time in hours, or None if no closed PRs
        """
        times = [pr["time_to_close_hours"] for pr in self.pr_data if pr["time_to_close_hours"]]
        return median(times) if times else None

    def get_prs_per_month(self) -> Dict[str, int]:
        """
        Get PR count grouped by month.

        Returns:
            Dictionary with month keys (YYYY-MM) and PR counts
        """
        monthly_counts = defaultdict(int)
        for pr in self.pr_data:
            month_key = pr["created_at"].strftime("%Y-%m")
            monthly_counts[month_key] += 1
        return dict(sorted(monthly_counts.items()))

    def get_prs_by_author(self) -> Dict[str, int]:
        """
        Get PR count by author.

        Returns:
            Dictionary with author usernames and their PR counts
        """
        author_counts = defaultdict(int)
        for pr in self.pr_data:
            if pr["author"]:
                author_counts[pr["author"]] += 1
        return dict(sorted(author_counts.items(), key=lambda x: x[1], reverse=True))

    def extract_work_items(self, description: str) -> Dict[str, List[str]]:
        """
        Extract work item references from PR description.

        Args:
            description: PR description text

        Returns:
            Dictionary with 'github_issues' and 'jira_tickets' lists
        """
        github_issues = set()
        jira_tickets = set()

        # Find GitHub issues
        github_issues.update(self.GITHUB_ISSUE_PATTERN.findall(description))
        github_issues.update(self.GITHUB_ISSUE_URL_PATTERN.findall(description))

        # Find Jira tickets
        jira_tickets.update(self.JIRA_PATTERN.findall(description))
        jira_tickets.update(self.JIRA_URL_PATTERN.findall(description))

        return {
            "github_issues": sorted(list(github_issues)),
            "jira_tickets": sorted(list(jira_tickets)),
        }

    def get_work_item_analysis(self) -> Dict[str, Any]:
        """
        Analyze work items referenced in PR descriptions.

        Returns:
            Dictionary with work item statistics
        """
        total_github_issues = set()
        total_jira_tickets = set()
        prs_with_work_items = 0

        for pr in self.pr_data:
            work_items = self.extract_work_items(pr["description"])
            if work_items["github_issues"] or work_items["jira_tickets"]:
                prs_with_work_items += 1
            total_github_issues.update(work_items["github_issues"])
            total_jira_tickets.update(work_items["jira_tickets"])

        return {
            "total_github_issues": len(total_github_issues),
            "total_jira_tickets": len(total_jira_tickets),
            "prs_with_work_items": prs_with_work_items,
            "prs_without_work_items": len(self.pr_data) - prs_with_work_items,
            "percentage_with_work_items": (
                (prs_with_work_items / len(self.pr_data) * 100) if self.pr_data else 0
            ),
        }

    def get_code_change_stats(self) -> Dict[str, Any]:
        """
        Get statistics about code changes.

        Returns:
            Dictionary with code change statistics
        """
        total_additions = sum(pr["additions"] for pr in self.pr_data)
        total_deletions = sum(pr["deletions"] for pr in self.pr_data)
        total_files_changed = sum(pr["changed_files"] for pr in self.pr_data)

        return {
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "total_files_changed": total_files_changed,
            "avg_additions_per_pr": total_additions / len(self.pr_data) if self.pr_data else 0,
            "avg_deletions_per_pr": total_deletions / len(self.pr_data) if self.pr_data else 0,
            "avg_files_per_pr": total_files_changed / len(self.pr_data) if self.pr_data else 0,
        }

    def get_monthly_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed breakdown of metrics per month.

        Returns:
            Dictionary with monthly statistics
        """
        monthly_data = defaultdict(list)

        # Group PRs by month
        for pr in self.pr_data:
            month_key = pr["created_at"].strftime("%Y-%m")
            monthly_data[month_key].append(pr)

        # Calculate metrics for each month
        monthly_breakdown = {}
        for month, prs in sorted(monthly_data.items()):
            analyzer = PRAnalyzer(prs)
            monthly_breakdown[month] = {
                "total_prs": len(prs),
                "merged": analyzer.get_merged_prs_count(),
                "closed_not_merged": analyzer.get_closed_prs_count(),
                "still_open": analyzer.get_open_prs_count(),
                "avg_time_to_close_hours": analyzer.get_average_time_to_close(),
                "work_items": analyzer.get_work_item_analysis(),
                "code_changes": analyzer.get_code_change_stats(),
                "top_authors": dict(
                    list(analyzer.get_prs_by_author().items())[:5]
                ),  # Top 5 contributors
            }

        return monthly_breakdown
