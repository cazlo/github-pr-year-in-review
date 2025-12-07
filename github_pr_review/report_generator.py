"""Report generator for creating summary documents."""

from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path


class ReportGenerator:
    """Generator for creating markdown summary reports."""

    def __init__(self, owner: str, repo: str, year: int):
        """
        Initialize the report generator.

        Args:
            owner: Repository owner
            repo: Repository name
            year: Year of the report
        """
        self.owner = owner
        self.repo = repo
        self.year = year

    def _format_time(self, hours: float) -> str:
        """
        Format hours into a human-readable string.

        Args:
            hours: Time in hours

        Returns:
            Formatted string (e.g., "2d 3h" or "5h 30m")
        """
        if hours is None:
            return "N/A"

        days = int(hours // 24)
        remaining_hours = int(hours % 24)
        minutes = int((hours % 1) * 60)

        if days > 0:
            return f"{days}d {remaining_hours}h"
        elif remaining_hours > 0:
            return f"{remaining_hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def generate_yearly_summary(
        self, analyzer, pr_data: List[Dict[str, Any]], output_path: str
    ) -> None:
        """
        Generate yearly summary report.

        Args:
            analyzer: PRAnalyzer instance
            pr_data: List of PR data dictionaries
            output_path: Path to save the report
        """
        avg_time = analyzer.get_average_time_to_close()
        median_time = analyzer.get_median_time_to_close()
        work_items = analyzer.get_work_item_analysis()
        code_stats = analyzer.get_code_change_stats()
        authors = analyzer.get_prs_by_author()

        report = f"""# GitHub PR Year in Review - {self.year}

**Repository:** {self.owner}/{self.repo}  
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Summary Statistics

### Pull Request Overview
- **Total PRs:** {analyzer.get_total_prs()}
- **Merged:** {analyzer.get_merged_prs_count()} ({analyzer.get_merged_prs_count() / max(analyzer.get_total_prs(), 1) * 100:.1f}%)
- **Closed (not merged):** {analyzer.get_closed_prs_count()}
- **Still Open:** {analyzer.get_open_prs_count()}

### Time to Close
- **Average:** {self._format_time(avg_time)}
- **Median:** {self._format_time(median_time)}

### Work Items & Value Delivery
- **GitHub Issues Referenced:** {work_items['total_github_issues']}
- **Jira Tickets Referenced:** {work_items['total_jira_tickets']}
- **PRs with Work Items:** {work_items['prs_with_work_items']} ({work_items['percentage_with_work_items']:.1f}%)
- **PRs without Work Items:** {work_items['prs_without_work_items']}

> **Insight:** {work_items['percentage_with_work_items']:.1f}% of PRs are linked to tracked work items, indicating {"strong" if work_items['percentage_with_work_items'] >= 70 else "moderate" if work_items['percentage_with_work_items'] >= 40 else "limited"} traceability between code changes and requirements.

### Code Changes
- **Total Lines Added:** {code_stats['total_additions']:,}
- **Total Lines Deleted:** {code_stats['total_deletions']:,}
- **Total Files Changed:** {code_stats['total_files_changed']:,}
- **Average per PR:**
  - Lines Added: {code_stats['avg_additions_per_pr']:.1f}
  - Lines Deleted: {code_stats['avg_deletions_per_pr']:.1f}
  - Files Changed: {code_stats['avg_files_per_pr']:.1f}

---

## Monthly Breakdown

"""

        # Add monthly PR counts
        prs_per_month = analyzer.get_prs_per_month()
        report += "### PRs per Month\n\n"
        report += "| Month | Count |\n|-------|-------|\n"
        for month, count in prs_per_month.items():
            report += f"| {month} | {count} |\n"

        report += "\n---\n\n## Top Contributors\n\n"
        report += "| Author | PRs |\n|--------|-----|\n"
        for author, count in list(authors.items())[:10]:
            report += f"| {author} | {count} |\n"

        report += "\n---\n\n## Key Insights\n\n"

        # Generate insights
        if avg_time:
            if avg_time < 24:
                report += "- ✅ **Fast PR turnaround:** PRs are closed quickly (< 1 day on average), indicating efficient review processes.\n"
            elif avg_time < 168:  # 1 week
                report += "- ✓ **Moderate PR turnaround:** PRs are closed within a week on average.\n"
            else:
                report += "- ⚠️ **Slow PR turnaround:** PRs take more than a week to close on average. Consider reviewing bottlenecks in the review process.\n"

        merge_rate = analyzer.get_merged_prs_count() / max(analyzer.get_total_prs(), 1) * 100
        if merge_rate > 80:
            report += "- ✅ **High merge rate:** Most PRs are successfully merged, indicating quality contributions.\n"
        elif merge_rate < 50:
            report += "- ⚠️ **Low merge rate:** Less than half of PRs are merged. Review PR quality and contribution guidelines.\n"

        if work_items["percentage_with_work_items"] < 40:
            report += "- ⚠️ **Limited work item linkage:** Consider improving traceability by linking PRs to issues or tickets.\n"

        # Save report
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report)

    def generate_monthly_breakdown(
        self, monthly_data: Dict[str, Dict[str, Any]], output_path: str
    ) -> None:
        """
        Generate detailed monthly breakdown report.

        Args:
            monthly_data: Dictionary of monthly statistics
            output_path: Path to save the report
        """
        report = f"""# Monthly Breakdown - {self.year}

**Repository:** {self.owner}/{self.repo}  
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""

        for month, data in monthly_data.items():
            month_name = datetime.strptime(month, "%Y-%m").strftime("%B %Y")
            report += f"## {month_name}\n\n"

            report += f"### Overview\n"
            report += f"- **Total PRs:** {data['total_prs']}\n"
            report += f"- **Merged:** {data['merged']}\n"
            report += f"- **Closed (not merged):** {data['closed_not_merged']}\n"
            report += f"- **Still Open:** {data['still_open']}\n"
            report += f"- **Avg Time to Close:** {self._format_time(data['avg_time_to_close_hours'])}\n\n"

            report += f"### Work Items\n"
            work_items = data["work_items"]
            report += f"- **GitHub Issues:** {work_items['total_github_issues']}\n"
            report += f"- **Jira Tickets:** {work_items['total_jira_tickets']}\n"
            report += f"- **PRs with Work Items:** {work_items['prs_with_work_items']} ({work_items['percentage_with_work_items']:.1f}%)\n\n"

            report += f"### Code Changes\n"
            code = data["code_changes"]
            report += f"- **Lines Added:** {code['total_additions']:,}\n"
            report += f"- **Lines Deleted:** {code['total_deletions']:,}\n"
            report += f"- **Files Changed:** {code['total_files_changed']:,}\n\n"

            if data["top_authors"]:
                report += f"### Top Contributors\n"
                for author, count in data["top_authors"].items():
                    report += f"- **{author}:** {count} PRs\n"

            report += "\n---\n\n"

        # Save report
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report)
