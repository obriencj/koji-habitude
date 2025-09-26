# koji-habitude Makefile
#
# Author: Christopher O'Brien <obriencj@gmail.com>
# License: GNU General Public License v3
# AI-Assistant: Claude 3.5 Sonnet via Cursor
# for hosting local docs preview


PYTHON ?= python3
TOX ?= tox
PORT ?= 8900


define checkfor
	@if ! which $(1) >/dev/null 2>&1 ; then \
		echo $(1) "is required, but not available" 1>&2 ; \
		exit 1 ; \
	fi
endef


.PHONY: build flake8 mypy twine test clean help tidy purge quicktest docs overview clean-docs preview-docs coverage docs-gen

# Default target
help:
	@echo "Available targets:"
	@echo "  build   - Create wheel distribution using bdist_wheel"
	@echo "  flake8  - Run flake8 linting"
	@echo "  mypy    - Run mypy type checking"
	@echo "  twine   - Check package with twine"
	@echo "  test    - Run tests with pytest"
	@echo "  quicktest - Run tests with system Python (faster)"
	@echo "  coverage - Run tests with coverage and generate HTML report"
	@echo "  tidy    - Tidy up stray python cache files"
	@echo "  clean   - Tidy up, then clean build artifacts"
	@echo "  purge   - Clean up, then purge tox environments"
	@echo "  docs    - Build sphinx docs"
	@echo "  docs-gen - Generate schema documentation from Pydantic models"
	@echo "  overview - Rebuild the overview from README.md"
	@echo "  clean-docs - Remove built docs"
	@echo "  preview-docs - Build and hosts docs locally"
	@echo "  help    - Show this help message"

# Build wheel distribution
build:
	$(TOX) -qe build

# Run flake8 linting
flake8:
	$(TOX) -qe flake8

# Run mypy type checking
mypy:
	$(TOX) -qe mypy

# Check package with twine
twine:  build
	$(TOX) -qe twine

# Run tests
test:
	$(TOX) -q

quicktest:
	$(TOX) -qe quicktest

# Run tests with coverage and generate HTML report
coverage:
	@mkdir -p build/coverage
	$(TOX) -qe coverage

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


docs-gen:	## Generate schema documentation from Pydantic models
	$(TOX) -qe docs-gen

docs: clean-docs docs/overview.rst	## Build sphinx docs
	$(TOX) -qe sphinx


overview: docs/overview.rst  ## rebuilds the overview from README.md


docs/overview.rst: README.md
	@if which pandoc >/dev/null 2>&1 ; then \
		echo "Using system pandoc..." ; \
		pandoc --from=markdown --to=rst -o $@ $< ; \
	else \
		echo "pandoc not found, using containerized version..." ; \
		podman run --rm -v "$(PWD):/workspace":Z -w /workspace \
			docker.io/pandoc/core:latest \
			--from=markdown --to=rst -o /workspace/$@ /workspace/$< ; \
	fi


clean-docs:	## Remove built docs
	@rm -rf build/sphinx


preview-docs: docs	## Build and hosts docs locally
	@$(PYTHON) -B -m http.server -d build/sphinx \
	  -b 127.0.0.1 $(PORT)


# The end.
