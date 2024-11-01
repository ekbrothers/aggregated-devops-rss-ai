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

## Repository Structure
```
├── .github
│   └── workflows
│       └── main.yml       # GitHub Actions workflow
├── dist/                  # Generated output directory (gitignored)
│   ├── index.html        # Generated HTML digest
│   ├── feed.xml          # Generated RSS feed
│   └── .nojekyll         # GitHub Pages configuration
├── main.py               # Main aggregator script
├── config.yml            # Configuration for feeds and sources
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Configuration
The `config.yml` file defines the sources to monitor:
- RSS feeds (e.g., GitHub releases, status pages)
- Manual sources requiring web scraping
- Source-specific configurations
- Additional settings for analysis

## Workflow
1. The GitHub Action runs weekly on Fridays
2. It fetches updates from all configured sources
3. Updates are filtered to the current week's range
4. Claude AI analyzes and summarizes the updates
5. Generates HTML and RSS output
6. Deploys to GitHub Pages

## GitHub Actions Workflow
```yaml
name: DevOps News Aggregator
on:
  schedule:
    - cron: '0 15 * * 5'  # Runs at 3 PM UTC every Friday
  workflow_dispatch:      # Allow manual triggers
  push:
    branches: [ main ]    # Run on main branch updates

permissions:
  contents: write
  pages: write
  id-token: write

jobs:
  aggregate-and-publish:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run aggregator
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python main.py
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./dist
          force_orphan: true
```

## Setup Requirements
1. GitHub repository with Actions enabled
2. Claude API key stored as a repository secret
3. GitHub Pages enabled on the repository
4. Python 3.x

## Dependencies
- feedparser: RSS feed parsing
- requests: HTTP requests
- anthropic: Claude AI API client
- beautifulsoup4: Web scraping
- jinja2: HTML template rendering
- PyYAML: Configuration file parsing

## Output
- HTML digest: `https://<username>.github.io/<repository>/`
- RSS feed: `https://<username>.github.io/<repository>/feed.xml`

## Known Limitations
- Web scraping might need updates if source websites change
- Claude API costs associated with usage
- Limited to weekly updates

## Future Enhancements
- Co
