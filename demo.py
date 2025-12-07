"""Demo script showing how to use the GitHub PR Review tool with mock data."""

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from github_pr_review.analyzer import PRAnalyzer
from github_pr_review.report_generator import ReportGenerator


def create_sample_pr_data():
    """Create sample PR data for demonstration."""
    base_date = datetime(2024, 1, 1)
    pr_data = []

    # Commit type patterns for variety
    commit_types = ["feat", "fix", "docs", "chore", "refactor", "test", "perf"]
    features = [
        "authentication system",
        "user dashboard",
        "API endpoint",
        "data validation",
        "caching layer",
        "notification service",
        "search functionality"
    ]

    # Generate sample PRs across the year
    for month in range(12):
        for i in range(5):  # 5 PRs per month
            created = base_date + timedelta(days=month * 30 + i * 3)
            closed = created + timedelta(hours=(24 + i * 12))
            
            pr_num = month * 5 + i + 1
            commit_type = commit_types[pr_num % len(commit_types)]
            feature = features[pr_num % len(features)]
            
            # Create commit messages with conventional commit format
            commit_messages = [
                f"{commit_type}: implement {feature}",
                f"{commit_type}: add tests for {feature}",
                f"docs: update README for {feature}",
            ]

            pr_data.append({
                "number": pr_num,
                "title": f"{commit_type}: {feature} #{pr_num}",
                "state": "closed" if i < 4 else "open",
                "created_at": created,
                "closed_at": closed if i < 4 else None,
                "merged_at": closed if i < 3 else None,
                "merged": i < 3,
                "author": f"user{i % 3 + 1}",
                "description": f"Implements #{'PROJ-' + str(100 + pr_num) if i % 2 else str(month * 10 + i)}\n\nThis PR adds {feature}.",
                "labels": ["enhancement" if i % 2 else "bug"],
                "time_to_close_hours": (closed - created).total_seconds() / 3600 if i < 4 else None,
                "url": f"https://github.com/demo/repo/pull/{pr_num}",
                "additions": 50 + i * 20,
                "deletions": 10 + i * 5,
                "changed_files": 2 + i,
                "commit_messages": commit_messages,
                "repository": "demo-org/demo-repo",  # Add repository field
            })

    return pr_data


def main():
    """Run the demo."""
    print("GitHub PR Year in Review - Demo")
    print("=" * 50)
    print()

    # Create sample data
    print("Generating sample PR data...")
    pr_data = create_sample_pr_data()
    print(f"Created {len(pr_data)} sample PRs")
    print()

    # Analyze the data
    print("Analyzing PR data...")
    analyzer = PRAnalyzer(pr_data)
    print()

    # Display some statistics
    print("Key Statistics:")
    print(f"  Total PRs: {analyzer.get_total_prs()}")
    print(f"  Merged: {analyzer.get_merged_prs_count()}")
    print(f"  Closed (not merged): {analyzer.get_closed_prs_count()}")
    print(f"  Still Open: {analyzer.get_open_prs_count()}")
    print()

    avg_time = analyzer.get_average_time_to_close()
    if avg_time:
        print(f"  Average Time to Close: {avg_time:.1f} hours ({avg_time / 24:.1f} days)")
    print()

    work_items = analyzer.get_work_item_analysis()
    print("Work Item Analysis:")
    print(f"  GitHub Issues: {work_items['total_github_issues']}")
    print(f"  Jira Tickets: {work_items['total_jira_tickets']}")
    print(f"  PRs with Work Items: {work_items['prs_with_work_items']} ({work_items['percentage_with_work_items']:.1f}%)")
    print()

    # Show code change statistics
    code_stats = analyzer.get_code_change_stats()
    print("Code Changes:")
    print(f"  Total Additions: {code_stats['total_additions']:,}")
    print(f"  Total Deletions: {code_stats['total_deletions']:,}")
    print(f"  Total Files Changed: {code_stats['total_files_changed']}")
    print(f"  Average Lines per PR: {code_stats['avg_additions_per_pr']:.1f}")
    print()

    # Show conventional commits analysis
    conv_commits = analyzer.get_conventional_commits_analysis()
    print("Conventional Commits:")
    print(f"  PRs with Conventional Commits: {conv_commits['prs_with_conventional_commits']} ({conv_commits['percentage_with_conventional']:.1f}%)")
    print(f"  Total Typed Commits: {conv_commits['total_typed_commits']}")
    if conv_commits['commit_types']:
        print("  Breakdown:")
        for commit_type, count in list(conv_commits['commit_types'].items())[:5]:  # Top 5
            print(f"    {commit_type}: {count}")
    if conv_commits['feat_fix_ratio']:
        print(f"  Feature/Fix Ratio: {conv_commits['feat_fix_ratio']:.2f}")
    print()

    # Show business insights
    business = analyzer.get_business_insights()
    print("Business Insights:")
    print(f"  Estimated Cost Savings: ${business['estimated_cost_savings']['total']:,.0f}")
    print(f"    - Bug Fixes: ${business['estimated_cost_savings']['bug_fixes']:,.0f}")
    print(f"    - Performance Improvements: ${business['estimated_cost_savings']['performance_improvements']:,.0f}")
    print(f"    - Test Additions: ${business['estimated_cost_savings']['test_additions']:,.0f}")
    print(f"  Velocity Score: {business['velocity_metrics']['velocity_score']}")
    print(f"  Merged Rate: {business['velocity_metrics']['merged_rate']:.1f}%")
    print(f"  Avg Lines per PR: {business['productivity_metrics']['avg_lines_per_pr']:.0f}")
    print()

    # Save raw PR data to JSON file
    print("Saving raw PR data...")
    output_dir = Path("demo_reports")
    output_dir.mkdir(exist_ok=True)
    
    raw_data_path = output_dir / "demo-org-demo-user-2024-raw-pr-data.json"
    with open(raw_data_path, 'w') as f:
        json.dump(pr_data, f, indent=2, default=str)
    print(f"✓ Raw PR data saved: {raw_data_path}")
    print()

    # Call the CLI with the raw PR data file
    print("Calling CLI with raw PR data file...")
    print()
    
    result = subprocess.run([
        "uv", "run", "python", "-m", "github_pr_review.cli",
        "demo-org",
        "demo-user",
        "--year", "2024",
        "--output-dir", str(output_dir),
        "--pr-data-file", str(raw_data_path)
    ], capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"Error: CLI execution failed with return code {result.returncode}")
        return
    
    print()
    print("✓ Demo completed successfully!")
    print(f"\nAll reports saved to: {output_dir.absolute()}")


if __name__ == "__main__":
    main()
