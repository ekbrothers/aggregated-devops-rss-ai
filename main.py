name: DevOps News Aggregator
on:
  schedule:
    - cron: '0 15 * * 5'  # Runs at 3 PM UTC every Friday
  workflow_dispatch:
  push:
    branches: [ main ]

jobs:
  aggregate-and-publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'
          
      - name: Install dependencies
        run: |
          pip install feedparser requests anthropic pyyaml beautifulsoup4 markdown jinja2
          
      - name: Run aggregator
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python main.py
        
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./dist
          enable_jekyll: false
