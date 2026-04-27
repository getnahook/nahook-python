# Contributing to nahook-python

Thanks for considering a contribution! A few important things to know first.

## Source of truth

This repository is a **subtree-split mirror** of the Python SDK from our private monorepo `getnahook/nahook`. PRs filed directly here **cannot be merged** — the next subtree-push from the monorepo will force-overwrite this branch.

## What we welcome

- **Bug reports** — open a GitHub issue with: reproduction steps, SDK version, Python version (`python3 --version`), OS.
- **Feature requests** — open an issue describing the use case and the API surface you'd want.
- **Small code suggestions** — paste a snippet in an issue and describe intent; we'll port it into the monorepo and credit you in the resulting commit.
- **Substantial patches** — email `support@nahook.com` first; we'll hand-port your change into the monorepo and credit you in the resulting commit.

## Local development

```bash
git clone https://github.com/getnahook/nahook-python
cd nahook-python
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q                       # full unit test suite
python -m build --wheel --sdist  # produces wheel + sdist for PyPI publish
```

`pyproject.toml` declares `requires-python = ">=3.9"`. SDK supports CPython 3.9 through latest stable.

### Code style

- Type hints encouraged but not enforced
- Tests use pytest + pytest-httpx + hypothesis (property-based)
- No required formatter; match surrounding style

## License

By contributing, you agree your changes are released under the [MIT License](LICENSE).
