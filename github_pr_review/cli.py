"""Command-line interface for GitHub PR Year in Review."""

import os
import sys
import click
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from github_pr_review.github_client import GitHubPRClient
from github_pr_review.analyzer import PRAnalyzer
from github_pr_review.report_generator import ReportGenerator


@click.command()
@click.argument("organization")
@click.argument("user")
@click.option(
    "--year",
    type=int,
    help="Year to analyze (default: current year)",
    default=None,
)
@click.option(
    "--token",
    help="GitHub personal access token (or set GITHUB_TOKEN env var)",
    default=None,
)
@click.option(
    "--output-dir",
    help="Directory to save reports (default: ./reports)",
    default="./reports",
)
def main(organization, user, year, token, output_dir):
    """
    Generate year-in-review summary for a GitHub user's PRs across an organization.

    \b
    Arguments:
        ORGANIZATION  GitHub organization name
        USER          GitHub username to analyze

    \b
    Examples:
        # Analyze user 'john' in 'myorg' for 2024
        github-pr-review myorg john --year 2024 --token ghp_xxx

        # Use environment variable for token
        export GITHUB_TOKEN=ghp_xxx
        github-pr-review myorg john --year 2024
    """
    # Get token from args or environment
    token = token or os.environ.get("GITHUB_TOKEN")
    if not token:
        click.echo(
            click.style("Error: GitHub token is required for organization access.", fg="red"),
            err=True,
        )
        click.echo("Set GITHUB_TOKEN environment variable or use --token flag.", err=True)
        sys.exit(1)

    # Determine year for report
    year = year if year else datetime.now().year

    click.echo(f"Analyzing PRs for user '{user}' in organization '{organization}'")
    click.echo(f"Year: {year}")
    click.echo()

    try:
        # Initialize client
        client = GitHubPRClient(token)
        
        # Get all repos where user has contributed
        click.echo("Fetching repositories...")
        repos = client.get_user_repos_in_org(organization, user)
        
        if not repos:
            click.echo(click.style(f"No repositories found where {user} has contributed.", fg="yellow"))
            return

        click.echo(f"Found {len(repos)} repositories with contributions")
        click.echo()

        # Fetch PRs from all repos
        pr_data_by_repo = {}
        all_pr_data = []
        
        with click.progressbar(repos, label="Fetching PRs from repositories") as bar:
            for repo in bar:
                repo_name = repo.full_name
                prs = client.get_prs_for_user_in_repo(repo, user, year)
                
                if prs:
                    pr_data = [client.extract_pr_data(pr, repo_name) for pr in prs]
                    pr_data_by_repo[repo_name] = pr_data
                    all_pr_data.extend(pr_data)

        if not all_pr_data:
            click.echo(click.style(f"No pull requests found for {user} in {year}.", fg="yellow"))
            return

        click.echo(f"\nFound {len(all_pr_data)} pull requests across {len(pr_data_by_repo)} repositories")
        click.echo()

        # Analyze data
        click.echo("Analyzing PR data...")
        
        # Create analyzers for each repo
        analyzer_by_repo = {}
        for repo_name, pr_data in pr_data_by_repo.items():
            analyzer_by_repo[repo_name] = PRAnalyzer(pr_data)
        
        # Create aggregated analyzer
        aggregated_analyzer = PRAnalyzer(all_pr_data)
        
        # Get monthly data by repo
        monthly_data_by_repo = {}
        for repo_name, analyzer in analyzer_by_repo.items():
            monthly_data_by_repo[repo_name] = analyzer.get_monthly_breakdown()
        
        # Get aggregated monthly data
        aggregated_monthly = aggregated_analyzer.get_monthly_breakdown()

        click.echo("Generating reports...")
        click.echo()

        # Generate reports
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        generator = ReportGenerator(organization, user, year)

        # 1. Generate JSON output
        json_path = output_dir / f"{organization}-{user}-{year}-data.json"
        generator.generate_json_output(
            pr_data_by_repo, analyzer_by_repo, aggregated_analyzer, str(json_path)
        )
        click.echo(f"✓ JSON data: {json_path}")

        # 2. Generate yearly summary by repo
        yearly_by_repo_path = output_dir / f"{organization}-{user}-{year}-by-repo-summary.md"
        generator.generate_yearly_summary_by_repo(
            pr_data_by_repo, analyzer_by_repo, str(yearly_by_repo_path)
        )
        click.echo(f"✓ Yearly summary (by repo): {yearly_by_repo_path}")

        # 3. Generate yearly summary aggregated
        yearly_agg_path = output_dir / f"{organization}-{user}-{year}-aggregated-summary.md"
        generator.generate_yearly_summary_aggregated(
            aggregated_analyzer, str(yearly_agg_path)
        )
        click.echo(f"✓ Yearly summary (aggregated): {yearly_agg_path}")

        # 4. Generate monthly breakdown by repo
        monthly_by_repo_path = output_dir / f"{organization}-{user}-{year}-by-repo-monthly.md"
        generator.generate_monthly_breakdown_by_repo(
            monthly_data_by_repo, str(monthly_by_repo_path)
        )
        click.echo(f"✓ Monthly breakdown (by repo): {monthly_by_repo_path}")

        # 5. Generate monthly breakdown aggregated
        monthly_agg_path = output_dir / f"{organization}-{user}-{year}-aggregated-monthly.md"
        generator.generate_monthly_breakdown_aggregated(
            aggregated_monthly, str(monthly_agg_path)
        )
        click.echo(f"✓ Monthly breakdown (aggregated): {monthly_agg_path}")

        click.echo()
        click.echo(click.style("Reports generated successfully!", fg="green", bold=True))

        # Show summary stats
        click.echo()
        click.echo("Summary:")
        click.echo(f"  Total PRs: {aggregated_analyzer.get_total_prs()}")
        click.echo(f"  Merged: {aggregated_analyzer.get_merged_prs_count()}")
        click.echo(f"  Repositories: {len(pr_data_by_repo)}")
        
        business = aggregated_analyzer.get_business_insights()
        click.echo(f"  Estimated Cost Savings: ${business['estimated_cost_savings']['total']:,.0f}")

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
