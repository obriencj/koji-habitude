"""
Sphinx configuration for the ud2 documentation.
"""

import importlib
from pathlib import Path


def load_setup():
    from configparser import ConfigParser

    global project
    global release
    global version
    global author
    global copyright

    conf = ConfigParser()
    conf.read(["../setup.cfg"])
    metadata = conf['metadata']

    project = metadata['name']
    release = metadata['version']
    version = '.'.join(release.split('.')[:2])
    author = metadata['author']
    copyright = f"{metadata['copyright_years']}, {author}"

load_setup()


def patch_sphinx_reports():
    # Fixes sphinx_reports type hinting issues which impact runtime without this
    # you'll see errors like:
    #
    # > WARNING: while setting up extension sphinx_reports: Failed to convert typing.Dict to a frozenset

    try:
        import sphinx_reports
    except ImportError:
        return

    ReportDomain = sphinx_reports.ReportDomain

    normalized = {}
    for key, (default, rebuild, config_type) in ReportDomain.configValues.items():
        origin = getattr(config_type, '__origin__', None)
        normalized_type = origin if origin is not None else config_type
        normalized[key] = (default, rebuild, normalized_type)

    ReportDomain.configValues = normalized

patch_sphinx_reports()


# General Sphinx configuration

extensions = [
    'myst_parser',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    # 'sphinx_autodoc_typehints',
    # 'sphinx_reports',
    'sphinxcontrib.mermaid',
]


templates_path = ['_templates']
exclude_patterns = ['build', 'Thumbs.db', '.DS_Store']

root_doc = 'index'

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# MyST / Markdown configuration
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}


# Intersphinx configuration

intersphinx_mapping = {
    "python": ('https://docs.python.org/3', None),

    'click': ('https://click.palletsprojects.com/en/stable/', None),
    'jinja2': ('https://jinja.palletsprojects.com/en/stable/', None),
    'pydantic': ('https://docs.pydantic.dev/latest', None),
}


# MyST / Markdown configuration

myst_enable_extensions = [
    'colon_fence',
    'deflist',
    'linkify',
]

myst_fence_as_directive = [
    'mermaid',
]


# Mermaid configuration

mermaid_version = '10.9.1'


# Autosummary configuration

autosummary_generate = True


# Autodoc configuration

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
    'exclude-members': 'field_validator',
}

suppress_warnings = [
    'autodoc.duplicate_object',
]


# Sphinx Reports configuration

# configuration for the Code Coverage report
report_codecov_packages = {
    'src': {
        'name': project,
        'json_report': 'build/coverage.json',
        'fail_below': 0,
        'levels': 'default',
    },
}


# The end.
