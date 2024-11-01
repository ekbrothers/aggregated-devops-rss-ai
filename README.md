# DevOps Platform Updates Aggregator

## Overview
This project automatically aggregates and synthesizes updates from various DevOps platforms and tools into a weekly digest. It uses Claude AI to analyze the updates and present the most important information in both RSS and HTML formats, hosted on GitHub Pages.

## Objective
DevOps engineers need to stay current with multiple platforms and tools, but manually checking various changelogs and release notes is time-consuming. This tool automates that process by:
- Collecting updates from multiple sources (RSS feeds and web pages)
- Using AI to analyze and prioritize the most important changes
- Generating a weekly digest with key takeaways and action items
- Publishing the digest in both RSS and HTML formats

## Features
- Weekly aggregation of updates from multiple sources
- AI-powered analysis of updates using Claude API
- Automatic categorization of updates by importance and type
- Weekly HTML digest hosted on GitHub Pages
- RSS feed for easy subscription
- Support for both RSS feeds and web scraping
- Weekly date-range filtering (Friday to Friday)

## File Structure
```
.
├── .github/workflows/    # GitHub Actions workflow configuration
│   └── aggregator.yaml   # Main workflow for running the aggregator
├── .gitignore           # Git ignore patterns
├── README.md            # Project documentation
├── analyze_with_claude.py # Claude AI analysis functionality
├── config.yml           # Configuration for RSS feeds and sources
├── main.py             # Main aggregator script
├── newsletter_template.html # HTML template for the weekly digest
└── requirements.txt     # Python package dependencies
```

### Key Files Explained:
- **analyze_with_claude.py**: Handles the interaction with Claude AI API, processes updates to generate summaries, impact assessments, and actionable insights for DevOps teams
- **config.yml**: Contains the configuration for all RSS feeds and manual sources to monitor, including URLs, source names, categories, and other settings
- **main.py**: Core script that orchestrates the entire aggregation process - fetches updates, coordinates analysis, and generates the final output
- **newsletter_template.html**: Jinja2 template that defines the structure and styling of the weekly HTML digest
- **.github/workflows/aggregator.yaml**: Defines the GitHub Actions workflow that runs weekly, executes the aggregator, and handles deployment to GitHub Pages

## Configuration
The `config.yml` file defines the sources to monitor:
* RSS feeds (e.g., GitHub releases, status pages)
* Manual sources requiring web scraping
* Source-specific configurations
* Additional settings for analysis

## Workflow
1. The GitHub Action runs weekly on Fridays
2. It fetches updates from all configured sources
3. Updates are filtered to the current week's range
4. Claude AI analyzes and summarizes the updates
5. Generates HTML and RSS output
6. Deploys to GitHub Pages

## Setup Requirements
1. GitHub repository with Actions enabled
2. Claude API key stored as a repository secret
3. GitHub Pages enabled on the repository
4. Python 3.x
