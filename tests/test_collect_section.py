"""Test cases for pytest plugin pytest-phmdoctest README.md docs."""
from pathlib import Path

import pytest


def test_collect_only_readme_tox(pytester, file_creator):
    """Configure tox.ini to collect README.md at root."""

    # Note tox.ini here and pytest.ini have the same format.
    pytester.makeini(
        """
        [pytest]
        addopts = --phmdoctest
        phmdoctest-collect =
            README.md
        """
    )
    assert Path("tox.ini").exists()
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("-v")
    rr.assert_outcomes(passed=3)
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::README.session_00001_line_24*",
            "*::README.py::test_code_10_output_17*",
            "*tests/test_example.py::test_example*",  #  pre-existing pytest file
        ],
        consecutive=True,
    )


def test_collect_only_readme_pytest(pytester, file_creator):
    """Configure pytest.ini to collect README.md at root."""

    # Note tox.ini and pytest.ini here have the same format.
    pytester.makefile(
        ".ini",
        pytest="""
        [pytest]
        addopts = --phmdoctest
        phmdoctest-collect =
            README.md
        """,
    )
    assert Path("pytest.ini").exists()
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("-v")
    rr.assert_outcomes(passed=3)
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::README.session_00001_line_24*",
            "*::README.py::test_code_10_output_17*",
            "*tests/test_example.py::test_example*",  #  pre-existing pytest file
        ],
        consecutive=True,
    )


def test_collect_only_readme_setup(pytester, file_creator):
    """Configure setup.cfg to collect README.md at root."""

    pytester.makefile(
        ".cfg",
        setup="""
        [tool:pytest]
        addopts = --phmdoctest
        phmdoctest-collect =
            README.md
        """,
    )
    assert Path("setup.cfg").exists()
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("-v")
    rr.assert_outcomes(passed=3)
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::README.session_00001_line_24*",
            "*::README.py::test_code_10_output_17*",
            "*tests/test_example.py::test_example*",  #  pre-existing pytest file
        ],
        consecutive=True,
    )


def test_collect_only_readme_pyproject(pytester, file_creator):
    """Configure pyproject.toml to collect README.md at root."""

    pytester.makefile(
        ".toml",
        pyproject="""
        [tool.pytest.ini_options]
        addopts = "--phmdoctest"
        phmdoctest-collect = [
            "README.md",
        ]
        """,
    )
    assert Path("pyproject.toml").exists()
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("-v")
    rr.assert_outcomes(passed=3)
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::README.session_00001_line_24*",
            "*::README.py::test_code_10_output_17*",
            "*tests/test_example.py::test_example*",  #  pre-existing pytest file
        ],
        consecutive=True,
    )


def test_collect_skip(pytester):
    """Collect section -s and --skip arg. Note single/double quote placement for .toml.

    Note the plugin does not accept single quoted phmdoctest args in the
    phmdoctest-collect section.
    """

    pytester.makeconftest('pytest_plugins = ["pytest_phmdoctest"]')
    pytester.makefile(
        ".toml",
        pyproject="""
        [tool.pytest.ini_options]
        addopts = "--phmdoctest"
        phmdoctest-collect = [
            'doc/example2.md --skip "Python 3.7" -sLAST',
        ]
        """,
    )
    assert Path("pyproject.toml").exists()
    pytester.mkdir("doc")
    pytester.copy_example("tests/markdown/example2.md")
    Path("example2.md").rename("doc/example2.md")
    assert Path("doc/example2.md").exists()
    rr = pytester.runpytest("-v")
    rr.assert_outcomes(passed=5)
    rr.stdout.fnmatch_lines(
        [
            "*::doc__example2.py::doc__example2.session_00001_line_75*",
            "*::doc__example2.py::test_code_9_output_14*",
            "*::doc__example2.py::test_code_37*",
            "*::doc__example2.py::test_code_44_output_51*",
            "*::doc__example2.py::test_code_87_output_94*",
        ],
        consecutive=True,
    )


def test_collect_setup(pytester):
    """Collect section --setup and --teardown args."""

    pytester.makefile(
        ".ini",
        pytest="""
        [pytest]
        addopts = --phmdoctest
        phmdoctest-collect =
            doc/setup.md --setup FIRST --teardown LAST
        """,
    )
    assert Path("pytest.ini").exists()
    pytester.mkdir("doc")
    pytester.copy_example("tests/markdown/setup.md")
    Path("setup.md").rename("doc/setup.md")
    assert Path("doc/setup.md").exists()
    rr = pytester.runpytest("-v")
    rr.assert_outcomes(passed=3)
    rr.stdout.fnmatch_lines(
        [
            "*::doc__setup.py::test_code_20_output_27*",
            "*::doc__setup.py::test_code_37_output_42*",
            "*::doc__setup.py::test_code_47_output_51*",
        ],
        consecutive=True,
    )


def test_collect_setup_doctest(pytester):
    """Collect section -s arg. Note single/double quote placement for .toml."""

    # Note tox.ini and pytest.ini here have the same format.
    pytester.makefile(
        ".ini",
        pytest="""
        [pytest]
        addopts = --phmdoctest
        phmdoctest-collect =
            doc/setup_doctest.md -u FIRST -d LAST --setup-doctest
        """,
    )
    assert Path("pytest.ini").exists()
    pytester.mkdir("doc")
    pytester.copy_example("tests/markdown/setup_doctest.md")
    Path("setup_doctest.md").rename("doc/setup_doctest.md")
    assert Path("doc/setup_doctest.md").exists()
    rr = pytester.runpytest("-v")
    rr.assert_outcomes(passed=6)
    rr.stdout.fnmatch_lines(
        [
            "*::doc__setup_doctest.py::doc__setup_doctest.session_00000*",
            "*::doc__setup_doctest.py::doc__setup_doctest.session_00001_line_69*",
            "*::doc__setup_doctest.py::doc__setup_doctest.session_00002_line_76*",
            "*::doc__setup_doctest.py::test_code_20_output_27*",
            "*::doc__setup_doctest.py::test_code_37_output_42*",
            "*::doc__setup_doctest.py::test_code_47_output_51*",
        ],
        consecutive=True,
    )


def test_auto_ignore_override(pytester, file_creator):
    """Collect section specifies file that would otherwise be auto-ignored."""

    pytester.makefile(
        ".toml",
        pyproject="""
        [tool.pytest.ini_options]
        addopts = "--phmdoctest"
        phmdoctest-collect = [
            'CONTRIBUTING.md',
        ]
        """,
    )
    assert Path("pyproject.toml").exists()
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("-v")
    rr.assert_outcomes(passed=2)
    rr.stdout.fnmatch_lines(
        [
            "*::CONTRIBUTING.py::test_nothing_passes*",
            "*tests/test_example.py::test_example*",
        ],
        consecutive=True,
    )


def test_collect_section_parse_failure(pytester, file_creator):
    """Parse collect section from pytest.ini and fail on last line."""

    pytester.makeini(
        """
        [pytest]
        addopts = --phmdoctest
        phmdoctest-collect =
            README.md
            doc/example*.md
            tests/bogus2.md  --bogus-command-line-option
        """
    )
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("-v")
    # Note-
    # fnmatch treats *, [, and ] as special characters for shell wildcards
    # so the usage details are not checked.
    #
    # pytest prints the warning to stdout.
    # The first phmdoctest-collect line collects README.md and generates
    # the first two test cases matched below.
    # The file test_example.py is collected by native pytest independently
    # of the plugin.
    #
    # Note: During development observed 7 calls with an identical message to
    # warnings.warn(). Only 1 was printed by pytester.
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::README.session_00001_line_24*",
            "*::README.py::test_code_10_output_17*",
            "*tests/test_example.py::test_example*",
            "*UserWarning: pytest-phmdoctest parse error on the following line:*",
            "*tests/bogus2.md  --bogus-command-line-option",
            "*usage: CollectSection*",
            "*Process a line of ini file phmdoctest-collect section.",
            "*positional arguments:",
            "*file_glob             Generate test file for matching markdown file.",
            "*optional arguments:",
            "*  -h, --help            show this help message and exit",
            "*  --skip TEXT, -s TEXT",
            "*  --fail-nocode",
            "*  --setup TEXT, -u TEXT",
            "*  --teardown TEXT, -d TEXT",
            "*  --setup-doctest",
        ],
        consecutive=False,
    )
    rr.assert_outcomes(passed=3)
