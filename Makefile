# The same four checks CI runs, in the same order. Run `make check` before pushing.
#
# This target exists because the alternative failed twice: running the linter but forgetting
# the formatter, and running a locally installed tool older than the one CI installs. Both
# produced a red build on a change that was correct.
#
# Everything goes through `python -m` so the tools always come from the interpreter holding the
# project's dependencies, rather than from whatever happens to be first on PATH.

PYTHON ?= python3

.PHONY: help install check lint format typecheck test examples clean web web-data js-install js-check e2e

help:
	@echo "install    install the package and dev tools"
	@echo "check      lint, format check, type check and the fast suite - what gates a push"
	@echo "check-all  the above plus every documented figure re-derived"
	@echo "claims     re-derive every number quoted in a README"
	@echo "format     rewrite files to the canonical format"
	@echo "examples   run every example script"
	@echo "web-data   regenerate the JSON the web interface reads"
	@echo "web        serve the web interface on http://127.0.0.1:8000/"
	@echo "js-check   JavaScript lint and unit/parity tests"
	@echo "e2e        browser tests (Chromium via Playwright)"

install:
	$(PYTHON) -m pip install -e ".[dev]"

# What a push should be gated on: lint, types and the fast suite.
check: lint typecheck test

# Everything, including the documented-figure verification. Minutes, not seconds.
check-all: lint typecheck test claims

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

format:
	$(PYTHON) -m ruff format .
	$(PYTHON) -m ruff check --fix .

typecheck:
	$(PYTHON) -m mypy

test:
	$(PYTHON) -m pytest -m "not slow" --cov --cov-report=term-missing

# Re-derives every number quoted in a README and runs all the example scripts. Slow on
# purpose: the gate policies are re-simulated.
claims:
	$(PYTHON) -m pytest -m slow -v

examples:
	@for script in examples/*.py; do echo "--- $$script"; $(PYTHON) "$$script" >/dev/null || exit 1; done
	@echo "all examples ran"

# The web interface: HTML, CSS and JavaScript over data exported from the Python library.
web-data:
	$(PYTHON) -m funilab.export web/data

web:
	node web/serve.mjs

js-install:
	npm ci

js-check:
	npx eslint web eslint.config.js
	npm test

e2e:
	npm run e2e

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage test-results
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
