"""Demo script showing how to use the GitHub PR Review tool with mock data."""

from datetime import datetime, timedelta
from github_pr_review.analyzer import PRAnalyzer
from github_pr_review.report_generator import ReportGenerator


def create_sample_pr_data():
    """Create sample PR data for demonstration."""
    base_date = datetime(2024, 1, 1)
    pr_data = []

    # Generate sample PRs across the year
    for month in range(12):
        for i in range(5):  # 5 PRs per month
            created = base_date + timedelta(days=month * 30 + i * 3)
            closed = created + timedelta(hours=(24 + i * 12))

            pr_data.append({
                "number": month * 5 + i + 1,
                "title": f"Feature/Fix #{month * 5 + i + 1}",
                "state": "closed" if i < 4 else "open",
                "created_at": created,
                "closed_at": closed if i < 4 else None,
                "merged_at": closed if i < 3 else None,
                "merged": i < 3,
                "author": f"user{i % 3 + 1}",
                "description": f"Implements #{'PROJ-' + str(100 + month * 5 + i) if i % 2 else str(month * 10 + i)}",
                "labels": ["enhancement" if i % 2 else "bug"],
                "time_to_close_hours": (closed - created).total_seconds() / 3600 if i < 4 else None,
                "url": f"https://github.com/demo/repo/pull/{month * 5 + i + 1}",
                "additions": 50 + i * 20,
                "deletions": 10 + i * 5,
                "changed_files": 2 + i,
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

    # Generate reports
    print("Generating reports...")
    generator = ReportGenerator("demo", "repo", 2024)
    monthly_breakdown = analyzer.get_monthly_breakdown()

    # Save reports to /tmp
    generator.generate_yearly_summary(analyzer, pr_data, "/tmp/demo-summary.md")
    generator.generate_monthly_breakdown(monthly_breakdown, "/tmp/demo-monthly.md")

    print("✓ Yearly summary: /tmp/demo-summary.md")
    print("✓ Monthly breakdown: /tmp/demo-monthly.md")
    print()
    print("Demo completed successfully!")


if __name__ == "__main__":
    main()
