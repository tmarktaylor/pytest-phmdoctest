"""Check dependencies in setup.cfg and requirements file are the same."""
import configparser
from pathlib import Path

import trove_classifiers
import yaml


def string_to_dependencies(text: str) -> set:
    """Return the set of pip dependencies from a multi-line string.

    Whitespace and empty lines are not significant.
    Comment lines are ignored.
    """
    lines = text.splitlines()
    lines = [line for line in lines if not line.startswith("#")]
    collapsed_lines = [line.replace(" ", "") for line in lines if line]
    items = set(collapsed_lines)
    if "" in items:
        items.remove("")  # empty string from blank lines
    return items


def setup_dependencies(section, option) -> set:
    """Extract set of dependencies from setup.cfg section/option."""
    config = configparser.ConfigParser()
    config.read("setup.cfg", encoding="utf-8")
    text = config.get(section, option)
    return string_to_dependencies(text)


def file_dependencies(filename: str) -> set:
    """Extract set of dependencies from a requirements.txt file."""
    text = Path(filename).read_text(encoding="utf-8")
    return string_to_dependencies(text)


def test_trove_classifiers():
    """Check the trove classifiers in setup.cfg."""
    config = configparser.ConfigParser()
    config.read("setup.cfg", encoding="utf-8")
    text = config.get("metadata", "classifiers")
    lines = text.splitlines()
    # remove comments and blank lines
    lines1 = [line for line in lines if not line.startswith("#")]
    lines2 = [line1 for line1 in lines1 if not line1 == ""]
    # No dupicates.
    items = set(lines2)
    assert len(items) == len(lines2)
    for trove_line in lines2:
        assert (
            trove_line in trove_classifiers.classifiers
        ), "Unknown classifier, check spelling."
        assert (
            trove_line not in trove_classifiers.deprecated_classifiers
        ), "Classifier is deprecated."


def test_install_requires():
    """setup.cfg install_requires == requirements.txt."""
    setup_values = setup_dependencies("options", "install_requires")
    requirements_values = file_dependencies("requirements.txt")
    assert setup_values == requirements_values


def test_extras_require_test():
    """setup.cfg extras_require|test key is up to date with tests/requirements.txt.

    The test key should have at least all the requirements from the
    requirements file.  It can have more.
    """
    setup_values = setup_dependencies("options.extras_require", "test")
    requirements_values = file_dependencies("tests/requirements.txt")
    assert requirements_values.issubset(setup_values)


def test_extras_require_inspect():
    """setup.cfg extras_require|inspect key == tests/requirements_inspect.txt."""
    setup_values = setup_dependencies("options.extras_require", "inspect")
    requirements_values = file_dependencies("tests/requirements_inspect.txt")
    assert setup_values == requirements_values


def test_extras_require_doc():
    """setup.cfg extras_require|doc key == docs/requirements.txt."""
    setup_values = setup_dependencies("options.extras_require", "docs")
    requirements_values = file_dependencies("doc/requirements.txt")
    assert setup_values == requirements_values


def test_readthedocs_python_version():
    """The build docs Python version == workflow step Python version."""
    rtd = yaml.safe_load(open(".readthedocs.yml", "r", encoding="utf-8"))
    workflow = yaml.safe_load(open(".github/workflows/ci.yml", "r", encoding="utf-8"))
    step = workflow["jobs"]["docs"]["steps"][1]
    assert "Setup Python" in step["name"]
    workflow_version = step["with"]["python-version"]
    assert rtd["python"]["version"] == workflow_version
