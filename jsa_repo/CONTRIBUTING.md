# Contributing

Contributions are welcome — bug reports, new scrapers, filter improvements, or documentation fixes.

## Development Setup

```bash
git clone https://github.com/<username>/job-search-agent.git
cd job-search-agent
./scripts/setup.sh
source .venv/bin/activate
```

## Adding a New Job Source

1. Create `job_agent/scrapers/my_source.py` inheriting `BaseScraper`.
2. Set `SOURCE_NAME` and `BASE_URL` as class attributes.
3. Implement `scrape(query: str) -> List[JobPosting]`.
4. Register in `job_agent/scrapers/__init__.py` → `ALL_SCRAPERS`.
5. Add a note to `CHANGELOG.md` under `[Unreleased]`.
6. Add a colour entry in `html_reporter.py` → `SOURCE_COLOURS`.

## Running Tests

```bash
pytest tests/ -v --tb=short
```

## Code Style

- PEP 8 compliant.
- Type hints on all public functions.
- Docstrings on all classes and public methods.
- Max line length: 100 characters.

## Pull Request Checklist

- [ ] Tests pass locally.
- [ ] New code has type hints.
- [ ] `CHANGELOG.md` updated under `[Unreleased]`.
- [ ] No secrets or credentials in any committed file.
