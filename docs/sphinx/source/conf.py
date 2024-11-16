# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import sys
import os

sys.path.insert(0, os.path.abspath('../../../src'))


project = 'ao-sol'
copyright = '2024, Miguel Fernandes'
author = 'Miguel Fernandes'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.mathjax",
    "nbsphinx",
    "nbsphinx_link",
    "sphinx_gallery.load_style",
    "autoapi.extension",
    #"sphinx.ext.napoleon",
]

suppress_warnings = ['autosectionlabel.*']

autoapi_dirs = ['../../../src/aosol']
autoapi_add_toctree_entry = True
# unused autoapi options 'private-members', 'special-members'
autoapi_options = ['members', 'undoc-members', 'show-inheritance', 'show-module-summary', 'imported-members',]

mathjax3_config = {'chtml': {'displayAlign': 'left',
                             'displayIndent': '2em'}}

templates_path = ['_templates']
exclude_patterns = []

language = 'pt_PT'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
