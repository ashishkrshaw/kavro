# Contributing to Kavro

Hey! Thanks for wanting to contribute. Here's how to do it.

## Found a Bug?

Open an issue and tell me:
- What you expected to happen
- What actually happened
- Steps to reproduce it
- Python version, OS, etc.

## Want to Add Something?

1. Open an issue first so we can discuss it
2. Fork the repo
3. Make your changes
4. Run the tests
5. Submit a PR

## Setting Up for Development

```bash
git clone https://github.com/YOUR_USERNAME/kavro.git
cd kavro

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-test.txt

cp .env.example .env
# Edit .env with your local settings
```

## Running Tests

Before submitting anything:

```bash
pytest app/tests/ -v
```

All tests should pass. If you added new functionality, add tests for it too.

## Code Style

Nothing fancy:
- Follow PEP 8
- Use type hints
- Keep functions small
- Add docstrings for public functions
- No magic numbers - use constants

I don't have a linter enforced, but please keep the code readable.

## Commit Messages

Just be clear:
- `fix: registration failing for long usernames`
- `feat: add message search endpoint`
- `docs: update deployment guide`

No need for elaborate conventions.

## PR Guidelines

- One feature/fix per PR
- Update tests if needed
- Update docs if needed
- Keep it focused

## Questions?

Open an issue or reach out to me on GitHub.

Thanks for helping make Kavro better!
