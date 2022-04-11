"""Test cases for pytest plugin pytest-phmdoctest README.md docs."""
from pathlib import Path


def test_collect_only_readme_tox(pytester, file_creator):
    """Configure tox.ini to collect README.md at root."""

    # Note tox.ini here and pytest.ini have the same format.
    pytester.makeini(
        """
        [pytest]
        addopts = --phmdoctest-docmod
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
            "*tests/test_example.py::test_example*",
        ],
        consecutive=True,
    )


def test_tox_has_doctest_options(pytester, file_creator):
    """Configure tox.ini to collect README.md at root."""

    # Note tox.ini here and pytest.ini have the same format.
    pytester.makeini(
        """
        [pytest]
        addopts = --phmdoctest-generate=.gendir --doctest-modules --ignore src
        phmdoctest-collect =
            README.md
        """
    )
    assert Path("tox.ini").exists()
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("-v", ".", ".gendir")
    rr.assert_outcomes(passed=3)
    rr.stdout.fnmatch_lines(
        [
            "*tests/test_example.py::test_example*",
            "*.gendir/test_README.py::test_README.session_00001_line_24*",
            "*.gendir/test_README.py::test_code_10_output_17*",
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
        addopts = --phmdoctest-docmod
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
            "*tests/test_example.py::test_example*",
        ],
        consecutive=True,
    )


def test_collect_only_readme_setup(pytester, file_creator):
    """Configure setup.cfg to collect README.md at root."""

    pytester.makefile(
        ".cfg",
        setup="""
        [tool:pytest]
        addopts = --phmdoctest-generate=.gendir
        phmdoctest-collect =
            README.md
        """,
    )
    assert Path("setup.cfg").exists()
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest(
        "-v", ".", ".gendir", "--doctest-modules", "--ignore", "src"
    )
    rr.assert_outcomes(passed=3)
    rr.stdout.fnmatch_lines(
        [
            "*tests/test_example.py::test_example*",
            "*.gendir/test_README.py::test_README.session_00001_line_24*",
            "*.gendir/test_README.py::test_code_10_output_17*",
        ],
        consecutive=True,
    )


def test_setup_has_doctest_options(pytester, file_creator):
    """Configure setup.cfg to collect README.md at root."""

    pytester.makefile(
        ".cfg",
        setup="""
        [tool:pytest]
        addopts = --phmdoctest-generate=.gendir --doctest-modules --ignore src
        phmdoctest-collect =
            README.md
        """,
    )
    assert Path("setup.cfg").exists()
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("-v", ".", ".gendir")
    rr.assert_outcomes(passed=3)
    rr.stdout.fnmatch_lines(
        [
            "*tests/test_example.py::test_example*",
            "*.gendir/test_README.py::test_README.session_00001_line_24*",
            "*.gendir/test_README.py::test_code_10_output_17*",
        ],
        consecutive=True,
    )


def test_collect_only_readme_pyproject(pytester, file_creator):
    """Configure pyproject.toml to collect README.md at root."""

    pytester.makefile(
        ".toml",
        pyproject="""
        [tool.pytest.ini_options]
        addopts = "--phmdoctest-generate=.gendir"
        phmdoctest-collect = [
            "README.md",
        ]
        """,
    )
    assert Path("pyproject.toml").exists()
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest(
        "-v", ".", ".gendir", "--doctest-modules", "--ignore", "src"
    )
    rr.assert_outcomes(passed=3)
    rr.stdout.fnmatch_lines(
        [
            "*tests/test_example.py::test_example*",
            "*.gendir/test_README.py::test_README.session_00001_line_24*",
            "*.gendir/test_README.py::test_code_10_output_17*",
        ],
        consecutive=True,
    )


def test_pyproject_has_doctest_options(pytester, file_creator):
    """Configure pyproject.toml to collect README.md at root."""

    pytester.makefile(
        ".toml",
        pyproject="""
        [tool.pytest.ini_options]
        addopts = "--phmdoctest-generate=.gendir --doctest-modules --ignore src"
        phmdoctest-collect = [
            "README.md",
        ]
        """,
    )
    assert Path("pyproject.toml").exists()
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("-v", ".", ".gendir")
    rr.assert_outcomes(passed=3)
    rr.stdout.fnmatch_lines(
        [
            "*tests/test_example.py::test_example*",
            "*.gendir/test_README.py::test_README.session_00001_line_24*",
            "*.gendir/test_README.py::test_code_10_output_17*",
        ],
        consecutive=True,
    )


def test_collect_skip(pytester):
    """Collect section -s and --skip arg. Note single/double quote placement for .toml.

    Note the plugin does not accept single quoted phmdoctest args in the
    phmdoctest-collect section.
    """

    pytester.makefile(
        ".toml",
        pyproject="""
        [tool.pytest.ini_options]
        addopts = "--phmdoctest-docmod"
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


def test_collect_fail_nocode(pytester):
    """Collect section --skip skips all, so --fail-nocode generates a failing test.

    This test shows how the option --fail-nocode causes a test failure
    when all the code blocks are skipped by the --skip options.
    --skip TEXT selects all blocks that contain TEXT.
    The --skip print selects 5 Python code blocks.
    """

    pytester.makefile(
        ".toml",
        pyproject="""
        [tool.pytest.ini_options]
        addopts = "--phmdoctest-docmod"
        phmdoctest-collect = [
            "doc/example2.md --skip print --skip Greetings --skip Fraction --fail-nocode",
        ]
        """,
    )
    assert Path("pyproject.toml").exists()
    pytester.mkdir("doc")
    pytester.copy_example("tests/markdown/example2.md")
    Path("example2.md").rename("doc/example2.md")
    assert Path("doc/example2.md").exists()
    rr = pytester.runpytest("-v")
    rr.assert_outcomes(failed=1)
    rr.stdout.fnmatch_lines(
        [
            "*::doc__example2.py::test_nothing_fails FAILED*",
        ],
        consecutive=True,
    )


def test_collect_setup(pytester):
    """Collect section --setup and --teardown args."""

    pytester.makefile(
        ".ini",
        pytest="""
        [pytest]
        addopts = --phmdoctest-docmod
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
        addopts = --phmdoctest-docmod
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


def test_collect_section_parse_failure(pytester, file_creator):
    """Parse collect section from pytest.ini and fail on last line.

    The first file tried is CONTRIBUTING.md. It does not the globs
    on the first two lines of the ini file.
    When the 3rd line is tried the parse error is detected.
    The plugin generates test file CONTRIBUTING.py which has one
    test called test_ini_failed which prints an error message to stdout
    and raises an assertion.

    README.md matches the first glob and collects 2 test cases that pass.
    The 4 files in the doc folder suffer the same fate as
    CONTRIBUTING.md and collect test files with the failing test.
    tests/test_example.py is collected normally with 1 passing test case.
    """
    pytester.makeini(
        """
        [pytest]
        addopts = --phmdoctest-docmod
        phmdoctest-collect =
            README.md
            doc/example*.md
            tests/bogus2.md  --bogus-command-line-option
        """
    )
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("-v")
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::README.session_00001_line_24*",
            "*::README.py::test_code_10_output_17*",
            "*::doc__directive2.py::test_ini_failed*",
            "*::doc__project.py::test_ini_failed*",
            "*tests/test_example.py::test_example*",
        ],
        consecutive=False,
    )
    rr.assert_outcomes(failed=2, passed=3)
