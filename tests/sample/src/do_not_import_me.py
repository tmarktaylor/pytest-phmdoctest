"""Raises an AssertionError if imported."""

# If a generated test file has docstrings that came from Markdown
# examples the user needs to call pytest with --doctest-modules option
# to test them.
# --doctest-modules imports modules to look for docstrings.
# This file simulates a user who does not want modules from their src
# folder imported in this manner.
assert False, "This file should not be imported."
