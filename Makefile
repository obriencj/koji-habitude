# koji-habitude Makefile
#
# Author: Christopher O'Brien <obriencj@gmail.com>
# License: GNU General Public License v3
# AI-Assistant: Claude 4.5 Sonnet via Cursor
# for hosting local docs preview


PYTHON ?= python3
TOX ?= tox
PORT ?= 8900

VERSION ?= $(shell $(PYTHON) -B setup.py --version 2>/dev/null)


define checkfor
	@if ! which $(1) >/dev/null 2>&1 ; then \
		echo $(1) "is required, but not available" 1>&2 ; \
		exit 1 ; \
	fi
endef


.PHONY: build flake8 mypy twine test clean help tidy purge quicktest docs overview clean-docs preview-docs coverage docs-gen archive

# Default target
help:
	@echo "Available targets:"
	@echo "  build   - Create wheel distribution using bdist_wheel"
	@echo "  archive - Create source tarball for RPM building"
	@echo "  flake8  - Run flake8 linting"
	@echo "  mypy    - Run mypy type checking"
	@echo "  twine   - Check package with twine"
	@echo "  test    - Run tests with pytest"
	@echo "  compat  - Run tests with pydantic v1.10"
	@echo "  quicktest - Run tests with system Python (faster)"
	@echo "  prepush - Run all tests and checks before pushing"
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


version:
	@$(PYTHON) -B setup.py --version 2>/dev/null

# Create source archive for RPM building
archive:
	if [ -z "$(VERSION)" ]; then \
		echo "Error: Could not determine version from setup.py" >&2 ; \
		exit 1 ; \
	fi ; \
	ARCHIVE="koji-habitude-$(VERSION).tar.gz" ; \
	echo "Creating archive: $$ARCHIVE" ; \
	git archive --format=tar.gz --prefix="koji-habitude-$(VERSION)/" \
		-o "$$ARCHIVE" HEAD ; \
	echo "Archive created successfully: $$ARCHIVE"

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

compat:
	$(TOX) -qe compat

prepush:
	$(TOX) -qe flake8,mypy,quicktest,compat

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


docs: clean-docs	## Build sphinx docs
	$(TOX) -qe sphinx


clean-docs:	## Remove built docs
	@rm -rf build/docs


preview-docs: docs	## Build and hosts docs locally
	@$(PYTHON) -B -m http.server -d build/docs \
	  -b 127.0.0.1 $(PORT)


preview-coverage: coverage	## Build and hosts coverage report locally
	@$(PYTHON) -B -m http.server -d build/coverage \
	  -b 127.0.0.1 $(PORT)


# The end.
