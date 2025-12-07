"""Command-line interface for GitHub PR Year in Review."""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from github_pr_review.github_client import GitHubPRClient
from github_pr_review.analyzer import PRAnalyzer
from github_pr_review.report_generator import ReportGenerator


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate a year-in-review summary for GitHub pull requests"
    )
    parser.add_argument("owner", help="Repository owner (username or organization)")
    parser.add_argument("repo", help="Repository name")
    parser.add_argument(
        "--year",
        type=int,
        help="Year to analyze (default: last 365 days from now)",
        default=None,
    )
    parser.add_argument(
        "--token",
        help="GitHub personal access token (or set GITHUB_TOKEN env var)",
        default=None,
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to save reports (default: ./reports)",
        default="./reports",
    )

    args = parser.parse_args()

    # Get token from args or environment
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        print(
            "Warning: No GitHub token provided. API rate limits will be stricter.",
            file=sys.stderr,
        )
        print(
            "Consider setting GITHUB_TOKEN environment variable or using --token flag.",
            file=sys.stderr,
        )

    # Determine year for report
    year = args.year if args.year else datetime.now().year

    print(f"Fetching PRs for {args.owner}/{args.repo}...")
    print(f"Year: {year if args.year else 'Last 365 days'}")

    try:
        # Fetch PR data
        client = GitHubPRClient(token)
        prs = client.get_prs_for_year(args.owner, args.repo, args.year)

        if not prs:
            print(f"No pull requests found for the specified period.")
            return

        print(f"Found {len(prs)} pull requests. Extracting data...")

        # Extract PR data
        pr_data = [client.extract_pr_data(pr) for pr in prs]

        print("Analyzing PRs...")

        # Analyze data
        analyzer = PRAnalyzer(pr_data)
        monthly_breakdown = analyzer.get_monthly_breakdown()

        print("Generating reports...")

        # Generate reports
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        generator = ReportGenerator(args.owner, args.repo, year)

        # Generate yearly summary
        yearly_path = output_dir / f"{args.owner}-{args.repo}-{year}-summary.md"
        generator.generate_yearly_summary(analyzer, pr_data, str(yearly_path))
        print(f"✓ Yearly summary: {yearly_path}")

        # Generate monthly breakdown
        monthly_path = output_dir / f"{args.owner}-{args.repo}-{year}-monthly.md"
        generator.generate_monthly_breakdown(monthly_breakdown, str(monthly_path))
        print(f"✓ Monthly breakdown: {monthly_path}")

        print("\nReports generated successfully!")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
