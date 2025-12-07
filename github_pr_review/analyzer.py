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
    
    # Pattern for conventional commits
    CONVENTIONAL_COMMIT_PATTERN = re.compile(
        r'^(feat|fix|docs?|hotfix|chore|refactor|test|ci|perf|style|build|revert)(\([^)]+\))?: .+',
        re.MULTILINE | re.IGNORECASE
    )
    COMMIT_TYPE_PATTERN = re.compile(
        r'^(feat|fix|docs?|hotfix|chore|refactor|test|ci|perf|style|build|revert)',
        re.IGNORECASE
    )
    
    # Mapping for fuzzy matches to canonical types
    COMMIT_TYPE_ALIASES = {
        'doc': 'docs',
        'hotfix': 'fix',
    }

    def __init__(self, pr_data: List[Dict[str, Any]]):
        """
        Initialize the analyzer with PR data.

        Args:
            pr_data: List of dictionaries containing PR data
        """
        self.pr_data = pr_data
    
    def _normalize_commit_type(self, commit_type: str) -> str:
        """
        Normalize commit type to canonical form.
        
        Args:
            commit_type: Raw commit type from regex match
            
        Returns:
            Normalized commit type
        """
        commit_type = commit_type.lower()
        return self.COMMIT_TYPE_ALIASES.get(commit_type, commit_type)

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
    
    def get_prs_by_repo(self) -> Dict[str, int]:
        """
        Get PR count by repository.

        Returns:
            Dictionary with repo names and their PR counts
        """
        repo_counts = defaultdict(int)
        for pr in self.pr_data:
            if "repo" in pr:
                repo_counts[pr["repo"]] += 1
        return dict(sorted(repo_counts.items(), key=lambda x: x[1], reverse=True))
    
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

    def extract_conventional_commit_types(self, pr: Dict[str, Any]) -> List[str]:
        """
        Extract conventional commit types from PR title, description, and commit messages.

        Args:
            pr: PR data dictionary

        Returns:
            List of commit types found (feat, fix, docs, etc.)
        """
        types = []
        
        # Check PR title
        title_match = self.COMMIT_TYPE_PATTERN.match(pr["title"])
        if title_match:
            types.append(self._normalize_commit_type(title_match.group(1)))
        
        # Check PR description
        for match in self.COMMIT_TYPE_PATTERN.finditer(pr["description"]):
            types.append(self._normalize_commit_type(match.group(1)))
        
        # Check commit messages
        if "commit_messages" in pr:
            for message in pr["commit_messages"]:
                match = self.COMMIT_TYPE_PATTERN.match(message)
                if match:
                    types.append(self._normalize_commit_type(match.group(1)))
        
        return types

    def get_conventional_commits_analysis(self) -> Dict[str, Any]:
        """
        Analyze conventional commit usage across PRs.

        Returns:
            Dictionary with conventional commit statistics
        """
        commit_type_counts = defaultdict(int)
        prs_with_conventional_commits = 0
        
        for pr in self.pr_data:
            types = self.extract_conventional_commit_types(pr)
            if types:
                prs_with_conventional_commits += 1
                for commit_type in types:
                    commit_type_counts[commit_type] += 1
        
        total_types = sum(commit_type_counts.values())
        feat_count = commit_type_counts.get("feat", 0)
        fix_count = commit_type_counts.get("fix", 0)
        
        return {
            "commit_types": dict(sorted(commit_type_counts.items(), key=lambda x: x[1], reverse=True)),
            "prs_with_conventional_commits": prs_with_conventional_commits,
            "percentage_with_conventional": (
                (prs_with_conventional_commits / len(self.pr_data) * 100) if self.pr_data else 0
            ),
            "total_typed_commits": total_types,
            "feat_count": feat_count,
            "fix_count": fix_count,
            "feat_fix_ratio": feat_count / fix_count if fix_count > 0 else None,
        }

    def get_business_insights(self) -> Dict[str, Any]:
        """
        Calculate business-oriented insights and cost savings metrics.

        Returns:
            Dictionary with business insights
        """
        conv_commits = self.get_conventional_commits_analysis()
        code_stats = self.get_code_change_stats()
        
        # Estimate cost savings
        # Assumptions: avg dev hourly rate, time saved per automation/fix
        avg_hourly_rate = 75  # USD (configurable)
        
        # Bug fixes save approximately 4 hours of debugging/support time each
        fix_count = conv_commits.get("fix_count", 0)
        estimated_bug_fix_savings = fix_count * 4 * avg_hourly_rate
        
        # Performance improvements save ongoing operational costs
        perf_count = conv_commits.get("commit_types", {}).get("perf", 0)
        estimated_perf_savings = perf_count * 8 * avg_hourly_rate  # 8h per perf improvement
        
        # Test additions improve quality and reduce future bugs
        test_count = conv_commits.get("commit_types", {}).get("test", 0)
        estimated_test_savings = test_count * 2 * avg_hourly_rate  # 2h per test addition
        
        total_estimated_savings = (
            estimated_bug_fix_savings + 
            estimated_perf_savings + 
            estimated_test_savings
        )
        
        # Calculate velocity metrics
        avg_time = self.get_average_time_to_close()
        velocity_score = "high" if avg_time and avg_time < 48 else "medium" if avg_time and avg_time < 168 else "low"
        
        return {
            "estimated_cost_savings": {
                "bug_fixes": estimated_bug_fix_savings,
                "performance_improvements": estimated_perf_savings,
                "test_additions": estimated_test_savings,
                "total": total_estimated_savings,
                "currency": "USD",
            },
            "velocity_metrics": {
                "avg_time_to_close_hours": avg_time,
                "velocity_score": velocity_score,
                "total_prs": len(self.pr_data),
                "merged_rate": (self.get_merged_prs_count() / len(self.pr_data) * 100) if self.pr_data else 0,
            },
            "productivity_metrics": {
                "avg_lines_per_pr": code_stats["avg_additions_per_pr"] + code_stats["avg_deletions_per_pr"],
                "total_code_changes": code_stats["total_additions"] + code_stats["total_deletions"],
            },
        }

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
                "conventional_commits": analyzer.get_conventional_commits_analysis(),
                "top_authors": dict(
                    list(analyzer.get_prs_by_author().items())[:5]
                ),  # Top 5 contributors
            }

        return monthly_breakdown
