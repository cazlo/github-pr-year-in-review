# GitHub PR Year in Review

A Python tool to analyze GitHub pull requests over the past year and generate comprehensive summary reports. The tool fetches PR data from the GitHub API, analyzes metrics like PR count, time to close, work item linkage, and generates both yearly summaries and monthly breakdowns.

## Features

- **Comprehensive PR Analysis**: Fetches and analyzes all pull requests from the specified repository
- **Time Metrics**: Calculates average and median time to close PRs
- **Work Item Tracking**: Identifies and analyzes links to GitHub issues and Jira tickets in PR descriptions
- **Value Delivery Insights**: Derives insights about traceability and work item linkage
- **Monthly Breakdown**: Generates detailed per-month statistics
- **Yearly Summary**: Creates a comprehensive yearly overview with key insights
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

```bash
# Analyze a repository for the last 365 days
python main.py owner repo

# Analyze a specific year
python main.py owner repo --year 2024

# With GitHub token for higher rate limits
python main.py owner repo --token YOUR_GITHUB_TOKEN

# Or use environment variable
export GITHUB_TOKEN=YOUR_GITHUB_TOKEN
python main.py owner repo
```

### Command Line Options

- `owner`: Repository owner (username or organization) - **required**
- `repo`: Repository name - **required**
- `--year`: Specific year to analyze (default: last 365 days)
- `--token`: GitHub personal access token (or set `GITHUB_TOKEN` env var)
- `--output-dir`: Directory to save reports (default: `./reports`)

### Examples

```bash
# Analyze PyGithub repository for 2024
python main.py PyGithub PyGithub --year 2024

# Analyze with custom output directory
python main.py microsoft vscode --year 2024 --output-dir ./my-reports

# Use environment variable for token
export GITHUB_TOKEN=ghp_your_token_here
python main.py facebook react --year 2024
```

## Output

The tool generates two markdown reports:

1. **Yearly Summary** (`{owner}-{repo}-{year}-summary.md`):
   - Total PR statistics (merged, closed, open)
   - Average and median time to close
   - Work item linkage analysis
   - Code change statistics
   - Monthly PR counts
   - Top contributors
   - Key insights and recommendations

2. **Monthly Breakdown** (`{owner}-{repo}-{year}-monthly.md`):
   - Detailed month-by-month statistics
   - Per-month work item analysis
   - Per-month code changes
   - Top contributors each month

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=github_pr_review

# Run specific test file
uv run pytest tests/test_analyzer.py
```

### Project Structure

```
github-pr-year-in-review/
├── github_pr_review/
│   ├── __init__.py
│   ├── github_client.py      # GitHub API interaction
│   ├── analyzer.py            # PR data analysis
│   ├── report_generator.py   # Report generation
│   └── cli.py                 # Command-line interface
├── tests/
│   ├── __init__.py
│   ├── test_github_client.py
│   ├── test_analyzer.py
│   └── test_report_generator.py
├── main.py                    # Entry point
├── pyproject.toml            # Project configuration
└── README.md
```

## GitHub Token

For better rate limits (5000 requests/hour vs 60), provide a GitHub Personal Access Token:

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate a new token with `repo` scope (or just `public_repo` for public repos)
3. Use it with `--token` flag or set `GITHUB_TOKEN` environment variable

## Requirements

- Python 3.12+
- PyGithub
- pytest (for testing)

## License

MIT License - see LICENSE file for details

