# Contributing to vidflow

## Development Setup

```bash
git clone https://github.com/weitzu-com/vidflow.git
cd vidflow
pip install -e ".[dev]"
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Code Style

- Python 3.9+ compatible
- Type hints on all public methods
- 100 char line limit (ruff enforced)

## Pull Request Process

1. Fork and create a feature branch
2. Add tests for new functionality
3. Ensure `python -m pytest tests/ -v` passes
4. Ensure `ruff check vidflow/` passes
5. Submit PR with description of changes

## Commit Convention

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `test:` test additions
- `refactor:` code restructuring
- `chore:` maintenance
