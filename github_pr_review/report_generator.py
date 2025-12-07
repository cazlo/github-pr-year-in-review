"""Report generator for creating summary documents and JSON output."""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from collections import defaultdict


class ReportGenerator:
    """Generator for creating markdown summary reports and JSON data."""

    def __init__(self, org: str, user: str, year: int):
        """
        Initialize the report generator.

        Args:
            org: Organization name
            user: GitHub username
            year: Year of the report
        """
        self.org = org
        self.user = user
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

    def _format_currency(self, amount: float) -> str:
        """Format currency amount."""
        return f"${amount:,.0f}"
    
    def _generate_commit_type_pie_chart(self, commit_types: Dict[str, int], total: int) -> str:
        """
        Generate a Mermaid pie chart for commit types.
        
        Args:
            commit_types: Dictionary of commit types and counts
            total: Total number of typed commits
            
        Returns:
            Mermaid pie chart markdown
        """
        if not commit_types:
            return ""
        
        chart = "```mermaid\n%%{init: {'theme':'base'}}%%\npie showData\n"
        chart += '    title Commit Type Distribution\n'
        for commit_type, count in commit_types.items():
            chart += f'    "{commit_type}" : {count}\n'
        chart += "```\n\n"
        return chart
    
    def _generate_monthly_throughput_chart(self, prs_per_month: Dict[str, int]) -> str:
        """
        Generate a Mermaid XY chart for monthly PR throughput.
        
        Args:
            prs_per_month: Dictionary of month keys and PR counts
            
        Returns:
            Mermaid XY chart markdown
        """
        if not prs_per_month:
            return ""
        
        chart = """
```mermaid
---
config:
  themeVariables:
    xyChart:
      plotColorPalette: '#00FF00, #FF0000'
---
xychart
"""
        chart += '    title "Monthly PR Throughput"\n'
        chart += '    x-axis ['
        
        # Add month labels
        month_labels = []
        for month in prs_per_month.keys():
            month_name = datetime.strptime(month, "%Y-%m").strftime("%b")
            month_labels.append(f'"{month_name}"')
        chart += ", ".join(month_labels)
        chart += ']\n'
        
        # Add PR counts
        chart += '    y-axis "PRs" 0 --> '
        max_count = max(prs_per_month.values()) if prs_per_month.values() else 10
        chart += f'{int(max_count * 1.2)}\n'
        chart += '    bar ['
        chart += ", ".join(str(count) for count in prs_per_month.values())
        chart += ']\n'
        chart += "```\n\n"
        return chart
    
    def _generate_repo_treemap(self, analyzer_by_repo: Dict[str, Any]) -> str:
        """
        Generate a Mermaid treemap showing commit types by repository.
        
        Args:
            analyzer_by_repo: Dictionary of repository analyzers
            
        Returns:
            Mermaid treemap markdown (or empty string if not enough data)
        """
        if not analyzer_by_repo:
            return ""
        
        # Build treemap in mermaid `treemap-beta` syntax.
        # Category = repository, items = top commit types with counts.
        if not analyzer_by_repo:
            return ""

        lines: List[str] = []
        lines.append("```mermaid")
        lines.append("treemap-beta")

        # For each repo, list top commit types (limit to top 5 per repo)
        for repo, analyzer in analyzer_by_repo.items():
            conv_commits = analyzer.get_conventional_commits_analysis()
            commit_types = conv_commits.get('commit_types', {})

            if not commit_types:
                # Still output the repo as a category with an empty placeholder
                lines.append(f'"{repo}"')
                continue

            # Get top 5 commit types per repo (name and count)
            top_types = sorted(commit_types.items(), key=lambda x: x[1], reverse=True)[:5]

            # Category header
            lines.append(f'"{repo}"')
            for name, count in top_types:
                # Indented item lines with value following the example
                lines.append(f'    "{name}": {count}')

        lines.append("```")
        lines.append("")

        return "\n".join(lines)

    def generate_json_output(
        self,
        pr_data_by_repo: Dict[str, List[Dict[str, Any]]],
        analyzer_by_repo: Dict[str, Any],
        aggregated_analyzer: Any,
        output_path: str,
    ) -> None:
        """
        Generate comprehensive JSON output with all gathered data.

        Args:
            pr_data_by_repo: PR data organized by repository
            analyzer_by_repo: Analyzer instances for each repo
            aggregated_analyzer: Aggregated analyzer across all repos
            output_path: Path to save the JSON file
        """
        # Build comprehensive data structure
        data = {
            "metadata": {
                "organization": self.org,
                "user": self.user,
                "year": self.year,
                "generated_at": datetime.now().isoformat(),
            },
            "summary": {
                "total_prs": aggregated_analyzer.get_total_prs(),
                "merged": aggregated_analyzer.get_merged_prs_count(),
                "closed_not_merged": aggregated_analyzer.get_closed_prs_count(),
                "open": aggregated_analyzer.get_open_prs_count(),
                "avg_time_to_close_hours": aggregated_analyzer.get_average_time_to_close(),
                "median_time_to_close_hours": aggregated_analyzer.get_median_time_to_close(),
            },
            "repositories": {},
            "aggregated_metrics": {
                "work_items": aggregated_analyzer.get_work_item_analysis(),
                "code_changes": aggregated_analyzer.get_code_change_stats(),
                "conventional_commits": aggregated_analyzer.get_conventional_commits_analysis(),
                "business_insights": aggregated_analyzer.get_business_insights(),
                "monthly_breakdown": aggregated_analyzer.get_monthly_breakdown(),
                "prs_by_author": aggregated_analyzer.get_prs_by_author(),
                "prs_per_month": aggregated_analyzer.get_prs_per_month(),
            },
        }

        # Add per-repository data
        for repo, analyzer in analyzer_by_repo.items():
            data["repositories"][repo] = {
                "total_prs": analyzer.get_total_prs(),
                "merged": analyzer.get_merged_prs_count(),
                "work_items": analyzer.get_work_item_analysis(),
                "code_changes": analyzer.get_code_change_stats(),
                "conventional_commits": analyzer.get_conventional_commits_analysis(),
                "prs_per_month": analyzer.get_prs_per_month(),
                "prs_by_author": analyzer.get_prs_by_author(),
            }

        # Save JSON
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def generate_yearly_summary_by_repo(
        self,
        pr_data_by_repo: Dict[str, List[Dict[str, Any]]],
        analyzer_by_repo: Dict[str, Any],
        output_path: str,
    ) -> None:
        """
        Generate detailed yearly summary broken down by repository.

        Args:
            pr_data_by_repo: PR data organized by repository
            analyzer_by_repo: Analyzer instances for each repo
            output_path: Path to save the report
        """
        report = f"""# 📊 GitHub PR Year in Review - {self.year} (By Repository)

**Organization:** {self.org}  
**User:** {self.user}  
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""

        for repo, analyzer in analyzer_by_repo.items():
            report += f"## 📦 {repo}\n\n"
            
            avg_time = analyzer.get_average_time_to_close()
            work_items = analyzer.get_work_item_analysis()
            code_stats = analyzer.get_code_change_stats()
            conv_commits = analyzer.get_conventional_commits_analysis()

            report += f"### 📊 Summary Statistics\n\n"
            report += f"- 🔢 **Total PRs:** {analyzer.get_total_prs()}\n"
            report += f"- ✅ **Merged:** {analyzer.get_merged_prs_count()}\n"
            report += f"- ❌ **Closed (not merged):** {analyzer.get_closed_prs_count()}\n"
            report += f"- 🔓 **Still Open:** {analyzer.get_open_prs_count()}\n"
            report += f"- ⏰ **Average Time to Close:** {self._format_time(avg_time)}\n\n"

            report += f"### 🏷️ Conventional Commits\n\n"
            report += f"- 📝 **PRs with Conventional Commits:** {conv_commits['prs_with_conventional_commits']} ({conv_commits['percentage_with_conventional']:.1f}%)\n"
            if conv_commits['commit_types']:
                report += f"- **Commit Type Breakdown:**\n"
                for commit_type, count in list(conv_commits['commit_types'].items())[:5]:
                    emoji = {'feat': '✨', 'fix': '🐛', 'docs': '📚', 'chore': '🔧', 'refactor': '♻️', 
                            'test': '✅', 'ci': '👷', 'perf': '⚡', 'style': '💄', 'build': '🏗️'}.get(commit_type, '📌')
                    report += f"  - `{emoji} {commit_type}`: {count}\n"
            if conv_commits['feat_fix_ratio'] is not None:
                report += f"- ⚖️ **Feat/Fix Ratio:** {conv_commits['feat_fix_ratio']:.2f}\n"
            report += "\n"

            report += f"### 🔗 Work Items\n\n"
            report += f"- 🔖 **GitHub Issues Referenced:** {work_items['total_github_issues']} \n"
            report += f"- 📋 **Jira Tickets Referenced:** {work_items['total_jira_tickets']} \n"
            report += f"- ✅ **PRs with Work Items:** {work_items['prs_with_work_items']} ({work_items['percentage_with_work_items']:.1f}%) \n\n"

            report += f"### 💻 Code Changes\n\n"
            report += f"- ➕ **Total Lines Added:** {code_stats['total_additions']:,} \n"
            report += f"- ➖ **Total Lines Deleted:** {code_stats['total_deletions']:,} \n"
            report += f"- 📄 **Total Files Changed:** {code_stats['total_files_changed']:,} \n\n"

            report += "---\n\n"

        # Save report
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report)

    def generate_yearly_summary_aggregated(
        self, aggregated_analyzer: Any, analyzer_by_repo: Dict[str, Any], output_path: str
    ) -> None:
        """
        Generate aggregated yearly summary across all repositories.

        Args:
            aggregated_analyzer: Analyzer with all PRs combined
            analyzer_by_repo: Dictionary of repository analyzers (for treemap)
            output_path: Path to save the report
        """
        avg_time = aggregated_analyzer.get_average_time_to_close()
        median_time = aggregated_analyzer.get_median_time_to_close()
        work_items = aggregated_analyzer.get_work_item_analysis()
        code_stats = aggregated_analyzer.get_code_change_stats()
        conv_commits = aggregated_analyzer.get_conventional_commits_analysis()
        business = aggregated_analyzer.get_business_insights()
        repos_by_count = aggregated_analyzer.get_prs_by_repo()
        
        # Format feat/fix ratio
        feat_fix_ratio_str = f"{conv_commits['feat_fix_ratio']:.2f}" if conv_commits['feat_fix_ratio'] is not None else "N/A"

        report = f"""# 📊 GitHub PR Year in Review - {self.year} (Aggregated)

**Organization:** {self.org}  
**User:** {self.user}  
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 📈 Executive Summary

### Pull Request Overview
- 🔢 **Total PRs:** {aggregated_analyzer.get_total_prs()}
- ✅ **Merged:** {aggregated_analyzer.get_merged_prs_count()} ({aggregated_analyzer.get_merged_prs_count() / max(aggregated_analyzer.get_total_prs(), 1) * 100:.1f}%)
- ❌ **Closed (not merged):** {aggregated_analyzer.get_closed_prs_count()}
- 🔓 **Still Open:** {aggregated_analyzer.get_open_prs_count()}
- 📦 **Repositories Contributed To:** {len(repos_by_count)}

### ⏱️ Time Metrics
- ⏰ **Average Time to Close:** {self._format_time(avg_time)}
- ⏰ **Median Time to Close:** {self._format_time(median_time)}
- {'🚀' if business['velocity_metrics']['velocity_score'] == 'high' else '⚡' if business['velocity_metrics']['velocity_score'] == 'medium' else '🐢'} **Velocity Score:** {business['velocity_metrics']['velocity_score'].upper()}

---

## 🏷️ Conventional Commits Analysis

- 📝 **PRs with Conventional Commits:** {conv_commits['prs_with_conventional_commits']} ({conv_commits['percentage_with_conventional']:.1f}%)
- 🔢 **Total Typed Commits:** {conv_commits['total_typed_commits']} 
- ✨ **Feature Commits:** {conv_commits['feat_count']}
- 🐛 **Bug Fix Commits:** {conv_commits['fix_count']} 
- ⚖️ **Feat/Fix Ratio:** {feat_fix_ratio_str} 

### Commit Type Breakdown

"""

        if conv_commits['commit_types']:
            for commit_type, count in conv_commits['commit_types'].items():
                percentage = (count / conv_commits['total_typed_commits'] * 100) if conv_commits['total_typed_commits'] else 0
                emoji = {'feat': '✨', 'fix': '🐛', 'docs': '📚', 'chore': '🔧', 'refactor': '♻️', 
                        'test': '✅', 'ci': '👷', 'perf': '⚡', 'style': '💄', 'build': '🏗️'}.get(commit_type, '📌')
                report += f"- {emoji} **{commit_type}:** {count} ({percentage:.1f}%) \n"
        
        # Add pie chart
        report += "\n" + self._generate_commit_type_pie_chart(conv_commits['commit_types'], conv_commits['total_typed_commits'])
        
        report += f"""
---

## 💰 Business Value & Cost Savings

### Estimated Cost Savings
- 🐛 **Bug Fixes:** {self._format_currency(business['estimated_cost_savings']['bug_fixes'])}
- ⚡ **Performance Improvements:** {self._format_currency(business['estimated_cost_savings']['performance_improvements'])}
- ✅ **Test Additions:** {self._format_currency(business['estimated_cost_savings']['test_additions'])}
- 💵 **Total Estimated Savings:** {self._format_currency(business['estimated_cost_savings']['total'])}

> **Note:** Cost estimates based on industry averages for time saved through automation, bug fixes, and performance improvements.

### 🚀 Velocity & Productivity
- ✅ **Merge Rate:** {business['velocity_metrics']['merged_rate']:.1f}%
- ⏰ **Average PR Cycle Time:** {self._format_time(business['velocity_metrics']['avg_time_to_close_hours'])}
- 📝 **Average Lines Changed per PR:** {business['productivity_metrics']['avg_lines_per_pr']:.0f}
- 📊 **Total Code Changes:** {business['productivity_metrics']['total_code_changes']:,} lines

---

## 🔗 Work Items & Traceability

 - 🔖 **GitHub Issues Referenced:** {work_items['total_github_issues']}
 - 📋 **Jira Tickets Referenced:** {work_items['total_jira_tickets']}
 - ✅ **PRs with Work Items:** {work_items['prs_with_work_items']} ({work_items['percentage_with_work_items']:.1f}%)
 - ⚠️ **PRs without Work Items:** {work_items['prs_without_work_items']}

> **Insight:** {work_items['percentage_with_work_items']:.1f}% of PRs are linked to tracked work items, indicating {"strong 💪" if work_items['percentage_with_work_items'] >= 70 else "moderate 👍" if work_items['percentage_with_work_items'] >= 40 else "limited 📉"} traceability between code changes and requirements.

---

## 💻 Code Changes

- ➕ **Total Lines Added:** {code_stats['total_additions']:,}
- ➖ **Total Lines Deleted:** {code_stats['total_deletions']:,}
- 📄 **Total Files Changed:** {code_stats['total_files_changed']:,}
- 📈 **Net Lines Changed:** {code_stats['total_additions'] - code_stats['total_deletions']:+,}

---

## 📦 Repository Contributions
"""

        for repo, count in list(repos_by_count.items())[:10]:
            report += f"- **{repo}:** {count} PRs\n"

        # Add treemap for repo contributions
        if analyzer_by_repo:
            report += "\n### 🗺️ Commit Types by Repository\n\n"
            report += self._generate_repo_treemap(analyzer_by_repo)

        report += "\n---\n\n## 📅 Monthly Activity\n\n"
        
        prs_per_month = aggregated_analyzer.get_prs_per_month()
        
        # Add monthly throughput chart
        report += self._generate_monthly_throughput_chart(prs_per_month)
        
        report += "| Month | Count |\n|-------|-------|\n"
        for month, count in prs_per_month.items():
            report += f"| {month} | {count} |\n"

        report += "\n---\n\n## 💡 Key Insights\n\n"

        # Generate insights
        if avg_time:
            if avg_time < 24:
                report += "- ✅ **Fast PR turnaround:** PRs are closed quickly (< 1 day on average).\n"
            elif avg_time < 168:
                report += "- ✓ **Moderate PR turnaround:** PRs are closed within a week on average.\n"
            else:
                report += "- ⚠️ **Slow PR turnaround:** Consider reviewing bottlenecks.\n"

        merge_rate = aggregated_analyzer.get_merged_prs_count() / max(aggregated_analyzer.get_total_prs(), 1) * 100
        if merge_rate > 80:
            report += "- ✅ **High merge rate:** Most PRs are successfully merged.\n"
        elif merge_rate < 50:
            report += "- ⚠️ **Low merge rate:** Review PR quality and contribution guidelines.\n"

        if conv_commits['percentage_with_conventional'] > 70:
            report += "- ✅ **Strong conventional commit adoption:** Good standardization of commit messages.\n"
        elif conv_commits['percentage_with_conventional'] < 30:
            report += "- ⚠️ **Limited conventional commit usage:** Consider adopting conventional commits for better changelog generation.\n"

        # Save report
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report)

    def generate_monthly_breakdown_by_repo(
        self, monthly_data_by_repo: Dict[str, Dict[str, Dict[str, Any]]], output_path: str
    ) -> None:
        """
        Generate monthly breakdown by repository.

        Args:
            monthly_data_by_repo: Monthly data organized by repository
            output_path: Path to save the report
        """
        report = f"""# 📅 Monthly Breakdown - {self.year} (By Repository)

**Organization:** {self.org}  
**User:** {self.user}  
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""

        for repo, monthly_data in monthly_data_by_repo.items():
            report += f"## 📦 {repo}\n\n"
            
            for month, data in monthly_data.items():
                month_name = datetime.strptime(month, "%Y-%m").strftime("%B %Y")
                report += f"### 📆 {month_name}\n\n"
                report += f"- 🔢 **Total PRs:** {data['total_prs']}\n"
                report += f"- ✅ **Merged:** {data['merged']}\n"
                report += f"- ⏰ **Avg Time to Close:** {self._format_time(data['avg_time_to_close_hours'])}\n"
                
                if 'conventional_commits' in data:
                    conv = data['conventional_commits']
                    report += f"- 📝 **Conventional Commits:** {conv['prs_with_conventional_commits']} PRs\n"
                
                report += "\n"
            
            report += "---\n\n"

        # Save report
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report)

    def generate_monthly_breakdown_aggregated(
        self, monthly_data: Dict[str, Dict[str, Any]], output_path: str
    ) -> None:
        """
        Generate aggregated monthly breakdown across all repositories.

        Args:
            monthly_data: Aggregated monthly statistics
            output_path: Path to save the report
        """
        report = f"""# 📅 Monthly Breakdown - {self.year} (Aggregated)

**Organization:** {self.org}  
**User:** {self.user}  
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""

        for month, data in monthly_data.items():
            month_name = datetime.strptime(month, "%Y-%m").strftime("%B %Y")
            report += f"## 📆 {month_name}\n\n"

            report += f"### 📊 Overview\n"
            report += f"- 🔢 **Total PRs:** {data['total_prs']}\n"
            report += f"- ✅ **Merged:** {data['merged']}\n"
            report += f"- ❌ **Closed (not merged):** {data['closed_not_merged']}\n"
            report += f"- 🔓 **Still Open:** {data['still_open']}\n"
            report += f"- ⏰ **Avg Time to Close:** {self._format_time(data['avg_time_to_close_hours'])}\n\n"

            if 'conventional_commits' in data:
                conv = data['conventional_commits']
                report += f"### 🏷️ Conventional Commits\n"
                report += f"- 📝 **PRs with Conventional Commits:** {conv['prs_with_conventional_commits']}\n"
                report += f"- ✨ **Feat Count:** {conv['feat_count']}\n"
                report += f"- 🐛 **Fix Count:** {conv['fix_count']}\n\n"

            report += f"### 🔗 Work Items\n"
            work_items = data["work_items"]
            report += f"- 🔖 **GitHub Issues:** {work_items['total_github_issues']}\n"
            report += f"- 📋 **Jira Tickets:** {work_items['total_jira_tickets']}\n"
            report += f"- ✅ **PRs with Work Items:** {work_items['prs_with_work_items']} ({work_items['percentage_with_work_items']:.1f}%)\n\n"

            report += f"### 💻 Code Changes\n"
            code = data["code_changes"]
            report += f"- ➕ **Lines Added:** {code['total_additions']:,}\n"
            report += f"- ➖ **Lines Deleted:** {code['total_deletions']:,}\n"
            report += f"- 📄 **Files Changed:** {code['total_files_changed']:,}\n\n"

            report += "\n---\n\n"

        # Save report
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report)
