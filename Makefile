# koji-habitude Makefile
#
# Author: Christopher O'Brien <obriencj@gmail.com>
# License: GNU General Public License v3
# AI-Assistant: Claude 3.5 Sonnet via Cursor

.PHONY: build flake8 mypy twine test clean help tidy purge quicktest

# Default target
help:
	@echo "Available targets:"
	@echo "  build   - Create wheel distribution using bdist_wheel"
	@echo "  flake8  - Run flake8 linting"
	@echo "  mypy    - Run mypy type checking"
	@echo "  twine   - Check package with twine"
	@echo "  test    - Run tests with pytest"
	@echo "  quicktest - Run tests with system Python (faster)"
	@echo "  tidy    - Tidy up stray python cache files"
	@echo "  clean   - Tidy up, then clean build artifacts"
	@echo "  purge   - Clean up, then purge tox environments"
	@echo "  help    - Show this help message"

# Build wheel distribution
build:
	tox -e build

# Run flake8 linting
flake8:
	tox -e flake8

# Run mypy type checking
mypy:
	tox -e mypy

# Check package with twine
twine:  build
	tox -e twine

# Run tests
test:
	tox

quicktest:
	tox -e quicktest

tidy:
	@rm -rf *.egg-info/
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -name "*.pyc" -delete

# Clean build artifacts
clean:  tidy
	@rm -rf build/
	@rm -rf dist/

purge:  clean
	@rm -rf .tox/

# The end.
