"""Tests for pytest versions before 6.2 using testdir fixture.

Show that DoctestModule API is compatible.
Show the generated test file is not using any new pytest features.
Show test files are properly collected.
"""

from pathlib import Path
import sys

import pytest

# Ignore pytest warnings from testdir using tests written for pytester.
ignore_writer = "ignore:.*TerminalReporter.writer attribute is deprecated.*"
ignore_copy_example = "ignore:.*testdir.copy_example is an experimental api.*"


@pytest.mark.filterwarnings(ignore_writer)
@pytest.mark.filterwarnings(ignore_copy_example)
def test_project_readme(testdir):
    """Test 2 tests pass on project's README.md"""
    testdir.copy_example("README.md")
    assert Path("README.md").exists()
    rr = testdir.runpytest("-v", "README.md", "--phmdoctest-docmod")
    rr.assert_outcomes(passed=2)
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::README.session_00001_line_179 PASSED*",
            "*::README.py::test_code_12_output_16 PASSED*",
        ],
        consecutive=True,
    )


@pytest.mark.filterwarnings(ignore_writer)
@pytest.mark.filterwarnings(ignore_copy_example)
def test_collect_root(testdir):
    """A single file at pytest root is collected and tested."""
    testdir.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
    testdir.copy_example("tests/sample/README.md")
    rr = testdir.runpytest("-v")
    assert rr.ret == pytest.ExitCode.OK
    rr.assert_outcomes(passed=2)
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::README.session_00001_line_24*",
            "*::README.py::test_code_10_output_17*",
        ],
        consecutive=True,
    )


@pytest.mark.filterwarnings(ignore_writer)
@pytest.mark.filterwarnings(ignore_copy_example)
def test_collect_subdir(testdir):
    """A single file at pytest root/doc is collected and tested."""
    testdir.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
    testdir.copy_example("tests/sample/doc/directive2.md")
    testdir.mkdir("doc")
    Path("directive2.md").rename("doc/directive2.md")
    rr = testdir.runpytest("-v")
    rr.assert_outcomes(passed=3)
    rr.stdout.fnmatch_lines(
        [
            "*::doc__directive2.py::test_code_25_output_32*",
            "*::doc__directive2.py::test_code_42_output_47*",
            "*::doc__directive2.py::test_code_52_output_56*",
        ],
        consecutive=True,
    )


@pytest.mark.skipif(sys.version_info < (3, 8), reason="requires >=py3.8")
@pytest.mark.filterwarnings(ignore_writer)
@pytest.mark.filterwarnings(ignore_copy_example)
def test_directive1(testdir):
    """Specify single .md file to collect on the command line."""
    testdir.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
    testdir.copy_example("tests/markdown/directive1.md")
    rr = testdir.runpytest("-v")
    assert rr.ret == pytest.ExitCode.OK
    rr.assert_outcomes(passed=3, skipped=1)
    rr.stdout.fnmatch_lines(
        [
            "*::directive1.py::directive1.doctest_print_coffee*",  # this is the doctest
            "*::directive1.py::test_code_23*",
            "*::directive1.py::test_mark_skip SKIPPED *",
            "*::directive1.py::test_i_ratio*",
        ],
    )


@pytest.mark.filterwarnings(ignore_writer)
@pytest.mark.filterwarnings(ignore_copy_example)
def test_one_session_block(testdir):
    """Collect a .md file that has just one interactive session block.

    Show phmdoctest.tool.detect_python_examples can detect a session block.
    """
    testdir.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
    testdir.copy_example("tests/markdown/one_session_block.md")
    rr = testdir.runpytest("-v")
    assert rr.ret == pytest.ExitCode.OK
    rr.assert_outcomes(passed=1)
    rr.stdout.fnmatch_lines(
        [
            "*::one_session_block.py::one_session_block.session_00001_line_8*",
        ],
        consecutive=True,
    )


@pytest.mark.filterwarnings(ignore_writer)
@pytest.mark.filterwarnings(ignore_copy_example)
def test_file_has_no_examples(testdir):
    """Collect a .md file that has no code or interactive session blocks."""
    testdir.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
    testdir.copy_example("CONTRIBUTING.md")
    rr = testdir.runpytest("-v")
    assert rr.ret == pytest.ExitCode.NO_TESTS_COLLECTED
    rr.assert_outcomes()
    rr.stdout.fnmatch_lines(
        [
            "*collected 0 items*",
        ],
        consecutive=True,
    )


@pytest.mark.filterwarnings(ignore_writer)
@pytest.mark.filterwarnings(ignore_copy_example)
def test_collect_setup(testdir):
    """Collect section --setup and --teardown args."""

    testdir.makefile(
        ".ini",
        pytest="""
        [pytest]
        addopts = --phmdoctest-docmod
        phmdoctest-collect =
            doc/setup.md --setup FIRST --teardown LAST
        """,
    )
    assert Path("pytest.ini").exists()
    testdir.mkdir("doc")
    testdir.copy_example("tests/markdown/setup.md")
    Path("setup.md").rename("doc/setup.md")
    assert Path("doc/setup.md").exists()
    rr = testdir.runpytest("-v")
    rr.assert_outcomes(passed=3)
    rr.stdout.fnmatch_lines(
        [
            "*::doc__setup.py::test_code_20_output_27*",
            "*::doc__setup.py::test_code_37_output_42*",
            "*::doc__setup.py::test_code_47_output_51*",
        ],
        consecutive=True,
    )


@pytest.mark.filterwarnings(ignore_writer)
@pytest.mark.filterwarnings(ignore_copy_example)
def test_collect_setup_doctest(testdir):
    """Collect section -s arg. Note single/double quote placement for .toml."""

    # Note tox.ini and pytest.ini here have the same format.
    testdir.makefile(
        ".ini",
        pytest="""
        [pytest]
        addopts = --phmdoctest-docmod
        phmdoctest-collect =
            doc/setup_doctest.md -u FIRST -d LAST --setup-doctest
        """,
    )
    assert Path("pytest.ini").exists()
    testdir.mkdir("doc")
    testdir.copy_example("tests/markdown/setup_doctest.md")
    Path("setup_doctest.md").rename("doc/setup_doctest.md")
    assert Path("doc/setup_doctest.md").exists()
    rr = testdir.runpytest("-v")
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


@pytest.mark.filterwarnings(ignore_writer)
@pytest.mark.filterwarnings(ignore_copy_example)
def test_pytest_ignore_one(testdir, file_creator):
    """Show that Markdown files can be ignored from the command line."""
    testdir.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
    file_creator.populate_all(pytester_object=testdir)
    rr = testdir.runpytest("-v", "--ignore", "doc/directive2.md")
    rr.assert_outcomes(passed=7)


@pytest.mark.filterwarnings(ignore_writer)
@pytest.mark.filterwarnings(ignore_copy_example)
def test_failing_doctest_item(testdir, file_creator):
    """Show a generated failing doctest."""

    file_creator.populate_all(pytester_object=testdir)
    contents = Path("README.md").read_text(encoding="utf-8")
    injected = contents.replace("<BLANKLINE>", "<BOGUS>")
    _ = Path("README.md").write_text(injected, encoding="utf-8")
    rr = testdir.runpytest("--phmdoctest-docmod", "-v")
    rr.assert_outcomes(failed=1, passed=9)
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::README.session_00001_line_24 FAILED*",
            "*::README.py::test_code_10_output_17 PASSED*",
            "*::doc__directive2.py::test_code_25_output_32 PASSED*",
            "*::doc__directive2.py::test_code_42_output_47 PASSED*",
            "*::doc__directive2.py::test_code_52_output_56 PASSED*",
            "*::doc__project.py::doc__project.session_00001_line_31 PASSED*",
            "*::doc__project.py::doc__project.session_00002_line_46 PASSED*",
            "*::doc__project.py::doc__project.session_00003_line_55 PASSED*",
            "*::doc__project.py::test_code_12_output_19 PASSED*",
            "*tests/test_example.py::test_example PASSED*",
        ],
        consecutive=True,
    )
    # Note- Using ? to match [ and ] of [doctest].
    rr.stdout.fnmatch_lines(
        [
            "* ?doctest? README.session_00001_line_24*",
        ],
        consecutive=True,
    )


@pytest.mark.filterwarnings(ignore_writer)
@pytest.mark.filterwarnings(ignore_copy_example)
def test_failing_python_item(testdir, file_creator):
    """Show a generated failing Python code example."""

    file_creator.populate_all(pytester_object=testdir)
    contents = Path("doc/directive2.md").read_text(encoding="utf-8")
    injected = contents.replace("== [1, 2, 3, 4]", "== [1, 2, 3, 4, 9999]")
    _ = Path("doc/directive2.md").write_text(injected, encoding="utf-8")
    rr = testdir.runpytest("--phmdoctest-docmod", "-v")
    rr.assert_outcomes(failed=1, passed=9)
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::README.session_00001_line_24 PASSED*",
            "*::README.py::test_code_10_output_17 PASSED*",
            "*::doc__directive2.py::test_code_25_output_32 PASSED*",
            "*::doc__directive2.py::test_code_42_output_47 PASSED*",
            "*::doc__directive2.py::test_code_52_output_56 FAILED*",
            "*::doc__project.py::doc__project.session_00001_line_31 PASSED*",
            "*::doc__project.py::doc__project.session_00002_line_46 PASSED*",
            "*::doc__project.py::doc__project.session_00003_line_55 PASSED*",
            "*::doc__project.py::test_code_12_output_19 PASSED*",
            "*tests/test_example.py::test_example PASSED*",
        ],
        consecutive=True,
    )
