# GitHub Copilot Instructions for github-pr-year-in-review

## Project Overview

This is a Python tool to analyze GitHub pull requests across an organization for a specific user and generate comprehensive year-in-review reports with business insights.

## Core Architecture

### Dependency Management
- **ALWAYS use `uv`** for Python dependency management (not pip)
- Commands: `uv add <package>`, `uv run <command>`, `uv sync`
- Configuration in `pyproject.toml`

### CLI Framework
- Uses **Click** (not argparse) for command-line interface
- Main entry point: `github_pr_review/cli.py`

### Testing
- Use **pytest** for all tests
- Run tests: `uv run pytest` or `uv run pytest -v`
- All tests must pass before merging

## Module Structure

### `github_client.py`
- PyGithub wrapper for API interaction
- Fetches PRs from all repositories in an organization for a specific user
- Supports private repositories (requires token with appropriate scopes)
- Extracts PR metadata: time to close, code changes, descriptions, commits

### `analyzer.py`
- Analyzes PR data and calculates metrics
- Extracts conventional commit types from:
  - PR descriptions
  - Individual commit messages
- Calculates:
  - PR counts by state/month/author/repo
  - Time-to-close statistics
  - feat/fix ratios and conventional commit breakdown
  - Work item references (GitHub issues `#123`, Jira tickets `PROJ-123`)
  - Business metrics (cost savings, velocity)

### `report_generator.py`
- Generates markdown reports and JSON output
- Creates 4 markdown reports:
  1. Yearly summary by org/user/repo (detailed per-repo)
  2. Yearly summary by org/user (aggregated across repos)
  3. Monthly breakdown by org/user/repo (detailed per-repo)
  4. Monthly breakdown by org/user (aggregated across repos)
- Creates comprehensive JSON with all gathered data

### `cli.py`
- Click-based CLI
- Arguments: `organization user --year YEAR --token TOKEN --output-dir DIR`
- Token required for accessing org repositories

## Key Features

### Conventional Commits Support
- Parses commit types: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `ci:`, `perf:`, `style:`
- Extracts from both PR descriptions and individual git commits
- Calculates ratios and insights (e.g., feat/fix ratio, code churn types)

### Work Item Tracking
- Extracts GitHub issue references: `#123`, `https://github.com/owner/repo/issues/123`
- Extracts Jira ticket references: `PROJ-123`, `https://company.atlassian.net/browse/PROJ-123`
- Calculates traceability percentages

### Business Insights
- Cost savings analysis based on automation, bug fixes, performance improvements
- Velocity metrics (PRs per sprint, lines of code productivity)
- Value delivery insights from work item linkage
- Team efficiency metrics

## Code Style

### Import Order
```python
# Standard library
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

# Third-party
import click
from github import Github

# Local
from github_pr_review.analyzer import PRAnalyzer
```

### Documentation
- Use docstrings for all public functions/classes
- Include type hints
- Document parameters and return values

### Error Handling
- Provide clear error messages
- Handle GitHub API exceptions gracefully
- Log progress for long-running operations

## Testing Guidelines

### Unit Tests
- Mock GitHub API responses
- Test edge cases (empty repos, no PRs, missing users)
- Use pytest fixtures for common test data
- Aim for high code coverage

### Test Files
- `tests/test_github_client.py` - API interaction tests
- `tests/test_analyzer.py` - Analysis and metrics tests
- `tests/test_report_generator.py` - Report generation tests

## Common Patterns

### Fetching Organization PRs
```python
# Get all repos in org where user has contributed
repos = client.get_user_repos_in_org(org, user)
for repo in repos:
    prs = client.get_prs_for_user(repo, user, year)
```

### Conventional Commit Parsing
```python
import re
CONVENTIONAL_COMMIT_PATTERN = re.compile(r'^(feat|fix|docs|chore|refactor|test|ci|perf|style)(\(.+\))?: .+')
```

### Aggregation
- Per-repo data stored separately for detailed reports
- Aggregated data combines metrics across all repos for org/user summary

## Output Structure

```
reports/
├── org-user-2024-by-repo-summary.md      # Detailed per-repo yearly
├── org-user-2024-aggregated-summary.md   # Aggregated yearly
├── org-user-2024-by-repo-monthly.md      # Detailed per-repo monthly
├── org-user-2024-aggregated-monthly.md   # Aggregated monthly
└── org-user-2024-data.json               # Complete JSON data
```

## Authentication

- GitHub token required (not optional) for org access
- Token needs scopes: `repo` (full control for private repos), `read:org`
- Set via `--token` flag or `GITHUB_TOKEN` environment variable

## Performance Considerations

- Use pagination for large orgs
- Cache API responses when possible
- Show progress bars for long operations
- Rate limit handling with exponential backoff

## Future Enhancements to Consider

- Support for multiple users in one run
- Time-series trend analysis
- Comparison between time periods
- Team-level aggregations
- Export to other formats (PDF, HTML)
- Integration with business intelligence tools
