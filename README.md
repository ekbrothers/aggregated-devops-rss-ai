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
- Dark mode support for better readability
- Automated code quality checks with flake8

## Repository Structure
```
.
├── src/                    # Source code directory
│   ├── aggregator/        # Core aggregation functionality
│   │   ├── config_loader.py  # Loads and validates configuration
│   │   ├── feed_fetcher.py   # Handles RSS feed fetching
│   │   ├── manual_fetcher.py # Handles web scraping for non-RSS sources
│   │   ├── news_aggregator.py # Coordinates the aggregation process
│   │   └── utils.py          # Shared utility functions
│   ├── analysis/         # LLM analysis components
│   │   └── analyze_with_claude.py # Claude AI integration and prompt handling
│   ├── assets/          # Static assets
│   │   └── icons/       # Platform and provider icons
│   ├── output/          # Output generation
│   │   ├── html_generator.py # HTML digest generation
│   │   └── rss_generator.py  # RSS feed generation
│   └── utils/           # Shared utilities
│       └── icon_mapping.py   # Maps providers to their icons
├── .github/workflows/    # GitHub Actions workflow configuration
│   └── aggregator.yaml   # Main workflow for running the aggregator
├── .flake8              # Flake8 linter configuration
├── config.yml           # Configuration for RSS feeds and sources
├── newsletter_template.html # HTML template for the weekly digest
├── requirements.txt     # Python package dependencies
└── run_aggregator.py    # Main entry point script
```

## Modular Architecture for LLM Integration

The project is structured to effectively integrate with Large Language Models (LLM), specifically Claude AI, with clear separation of concerns:

### 1. Data Collection Layer (`src/aggregator/`)
- **config_loader.py**: Validates and loads source configurations
- **feed_fetcher.py**: Handles RSS feed parsing and normalization
- **manual_fetcher.py**: Manages web scraping for non-RSS sources
- **news_aggregator.py**: Orchestrates the collection process
- **utils.py**: Provides shared functionality for data handling

### 2. LLM Analysis Layer (`src/analysis/`)
- **analyze_with_claude.py**: Core LLM integration that:
  - Structures prompts for effective analysis
  - Handles communication with Claude API
  - Processes responses into structured data
  - Generates summaries and impact assessments
  - Extracts key changes and action items

### 3. Output Generation Layer (`src/output/`)
- **html_generator.py**: Generates the HTML digest with:
  - Platform-specific sections
  - Impact-level highlighting
  - Dark mode support
  - Responsive design
- **rss_generator.py**: Creates RSS feeds for subscription

### 4. Asset Management (`src/assets/` & `src/utils/`)
- Maintains consistent branding
- Maps platforms to their icons
- Provides visual context for different platforms

## LLM Workflow
1. **Data Collection**:
   - Aggregator modules collect updates from configured sources
   - Data is normalized into a consistent format
   - Updates are filtered to the current week's range

2. **LLM Analysis**:
   - Updates are batched and structured for Claude
   - Prompts are generated with specific analysis goals
   - Claude analyzes and returns structured insights
   - Results are parsed and validated

3. **Content Generation**:
   - Analysis results are formatted for presentation
   - HTML digest is generated with visual hierarchy
   - RSS feed is created for subscriptions
   - Content is optimized for readability

## Setup Requirements
1. GitHub repository with Actions enabled
2. Claude API key stored as a repository secret
3. GitHub Pages enabled on the repository
4. Python 3.x and required packages

## Configuration
The `config.yml` file defines:
- RSS feed sources
- Manual scraping targets
- Platform-specific settings
- Analysis parameters
- Output preferences

### Code Quality
The project uses flake8 for code quality enforcement with the following configuration:
- Maximum line length: 100 characters
- Maximum complexity: 10
- Ignores specific rules:
  - W503/W504: Line break before/after binary operator
  - E402: Module level import not at top of file
- Special handling for `__init__.py` files
- Configuration stored in `.flake8` file

## GitHub Actions Workflow
The workflow in `.github/workflows/aggregator.yaml`:
1. Runs code quality checks with flake8
2. Runs weekly on Fridays (if linting passes)
3. Executes the aggregator script
4. Processes updates through Claude
5. Generates HTML and RSS output
6. Deploys to GitHub Pages
