# GitHub PR Year in Review

A Python tool to analyze GitHub pull requests across an organization for a specific user and generate comprehensive year-in-review reports with business insights, conventional commits analysis, and cost savings estimates.

## Features

- **Organization-Wide Analysis**: Fetches PRs from all repositories in an organization where a specific user has contributed
- **Comprehensive PR Analysis**: Analyzes all pull requests with detailed metrics
- **Conventional Commits Support**: Extracts and analyzes commit types (feat, fix, docs, etc.) from PR titles, descriptions, and commit messages
- **Business Insights**: Calculates cost savings from bug fixes, performance improvements, and test additions
- **Work Item Tracking**: Identifies and analyzes links to GitHub issues and Jira tickets
- **Multiple Report Types**: Generates 4 markdown reports and 1 JSON file:
  1. Yearly summary by repository (detailed per-repo)
  2. Yearly summary aggregated (combined across all repos)
  3. Monthly breakdown by repository
  4. Monthly breakdown aggregated
  5. Complete JSON data export
- **Time Metrics**: Calculates average and median time to close PRs, velocity scores
- **Code Change Statistics**: Tracks lines added, deleted, and files changed

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Install uv if you haven't already
pip install uv

# Clone the repository
git clone https://github.com/cazlo/github-pr-year-in-review.git
cd github-pr-year-in-review

# Install dependencies
uv sync
```

## Usage

### Basic Usage

**Note:** A GitHub personal access token is **required** for accessing organization repositories.

```bash
# Analyze a user's PRs in an organization
uv run python main.py ORGANIZATION USER --year 2024 --token YOUR_GITHUB_TOKEN

# Or use environment variable
export GITHUB_TOKEN=YOUR_GITHUB_TOKEN
uv run python main.py myorg john --year 2024
```

### Command Line Options

- `ORGANIZATION`: GitHub organization name - **required**
- `USER`: GitHub username to analyze - **required**
- `--year`: Specific year to analyze (default: current year)
- `--token`: GitHub personal access token (or set `GITHUB_TOKEN` env var)
- `--output-dir`: Directory to save reports (default: `./reports`)

### Examples

```bash
# Analyze john's PRs in myorg for 2024
export GITHUB_TOKEN=ghp_your_token_here
uv run python main.py myorg john --year 2024

# Use custom output directory
uv run python main.py acme-corp jane --year 2024 --output-dir ./jane-review

# Analyze current year (2025)
uv run python main.py myorg alex
```

## Output

The tool generates 5 files in the output directory:

### Markdown Reports

1. **`{org}-{user}-{year}-by-repo-summary.md`**: Detailed yearly summary broken down by each repository
2. **`{org}-{user}-{year}-aggregated-summary.md`**: Executive summary aggregated across all repositories with:
   - Executive summary with PR counts, merge rates, velocity score
   - Conventional commits analysis with feat/fix ratios
   - Business value & cost savings estimates
   - Work item traceability analysis
   - Code changes overview
   - Repository contributions
   - Monthly activity trends
   - Key insights and recommendations

3. **`{org}-{user}-{year}-by-repo-monthly.md`**: Monthly breakdown by repository
4. **`{org}-{user}-{year}-aggregated-monthly.md`**: Monthly breakdown aggregated across all repositories

### JSON Data

5. **`{org}-{user}-{year}-data.json`**: Complete data export containing:
   - All PR data by repository
   - Aggregated metrics
   - Monthly breakdowns
   - Conventional commits analysis
   - Business insights
   - Work item analysis

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=github_pr_review

# Run specific test file
uv run pytest tests/test_analyzer.py -v
```

### Project Structure

```
github-pr-year-in-review/
├── .github/
│   └── copilot-instructions.md   # Development guidelines for Copilot
├── github_pr_review/
│   ├── __init__.py
│   ├── github_client.py          # GitHub API interaction (org-wide)
│   ├── analyzer.py                # PR analysis with conventional commits
│   ├── report_generator.py       # Multi-format report generation
│   └── cli.py                     # Click-based CLI
├── tests/
│   ├── __init__.py
│   ├── test_github_client.py
│   ├── test_analyzer.py
│   └── test_report_generator.py
├── main.py                        # Entry point
├── pyproject.toml                # Project configuration (uv)
└── README.md
```

## GitHub Token

A GitHub Personal Access Token is **required** (not optional) for accessing organization repositories.

### Required Token Scopes:
- `repo` - Full control of private repositories
- `read:org` - Read org and team membership

### Creating a Token:
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate a new token with the required scopes
3. Use it with `--token` flag or set `GITHUB_TOKEN` environment variable

## Conventional Commits

The tool recognizes and analyzes these conventional commit types:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `chore:` - Maintenance tasks
- `refactor:` - Code refactoring
- `test:` - Test additions/changes
- `ci:` - CI/CD changes
- `perf:` - Performance improvements
- `style:` - Code style changes
- `build:` - Build system changes
- `revert:` - Reverts

The tool extracts these from:
- PR titles
- PR descriptions
- Individual commit messages

## Business Insights

The tool calculates estimated cost savings based on:
- **Bug Fixes**: ~4 hours saved per fix (debugging/support time)
- **Performance Improvements**: ~8 hours saved per improvement
- **Test Additions**: ~2 hours saved per test (future bug prevention)

Default hourly rate: $75 USD (industry average for software engineering)

## Requirements

- Python 3.12+
- uv for dependency management
- click for CLI
- PyGithub for GitHub API access
- pytest for testing

## License

MIT License - see LICENSE file for details

