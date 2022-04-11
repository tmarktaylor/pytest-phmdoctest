"""Test cases for --phmdoctest-docmod."""
from packaging.version import Version
from pathlib import Path

import _pytest.doctest
import pytest


def test_collect_root(pytester):
    """A single file at pytest root is collected and tested."""
    pytester.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
    pytester.copy_example("tests/sample/README.md")
    rr = pytester.runpytest("-v")
    assert rr.ret == pytest.ExitCode.OK
    rr.assert_outcomes(passed=2)
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::README.session_00001_line_24*",
            "*::README.py::test_code_10_output_17*",
        ],
        consecutive=True,
    )


def test_collect_subdir(pytester):
    """A single file at pytest root/doc is collected and tested."""
    pytester.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
    pytester.copy_example("tests/sample/doc/directive2.md")
    pytester.mkdir("doc")
    Path("directive2.md").rename("doc/directive2.md")
    rr = pytester.runpytest("-v")
    rr.assert_outcomes(passed=3)
    rr.stdout.fnmatch_lines(
        [
            "*::doc__directive2.py::test_code_25_output_32*",
            "*::doc__directive2.py::test_code_42_output_47*",
            "*::doc__directive2.py::test_code_52_output_56*",
        ],
        consecutive=True,
    )


pytest_version = Version(pytest.__version__)
PYTEST_LT_7 = pytest_version < Version("7.0")


@pytest.mark.skipif(PYTEST_LT_7, reason="n/a pytest <= 7")
def test_import_doctest_module_fails(pytester, monkeypatch):
    """Cause import of _pytest.doctest.DoctestModule to fail.

    Verify logic to handle DoctestModule.from_parent() raising an exception.
    Note that _pytest.doctest.DoctestModule is not part of the pytest
    public API (not imported by import pytest).
    If a future pytest version changes the function or parameters or
    class the code tested here will show the root cause of the problem.
    """
    monkeypatch.setattr(_pytest.doctest, "DoctestModule", None)
    pytester.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
    pytester.copy_example("tests/markdown/one_session_block.md")
    rr = pytester.runpytest("-v")
    assert rr.ret == pytest.ExitCode.TESTS_FAILED
    rr.assert_outcomes(failed=1)
    rr.stdout.fnmatch_lines(
        [
            "*::one_session_block.py::test_unable_to_collect_doctests FAILED*",
            "*built from one_session_block.md*",
            "*pytest_phmdoctest.collectors.make_doctest_module() raised*",
            "*Try using --phmdoctest-generate option.*",
        ],
        consecutive=False,
    )


class MockDoctestModule:
    """Method from_parent takes 1 more arg than caller expects.

    Return an object that is incompatible with DoctestModule.
    Manually observed it cause pytest ExitCode.INTERRUPTED.
    This implies that args/parameter mismatch raised TypeError.
    """

    def from_parent(self, parent, path, extra_arg):
        return 99


@pytest.mark.skipif(PYTEST_LT_7, reason="n/a pytest <= 7")
def test_bad_doctest_module(pytester, monkeypatch):
    """Inject a DoctestModule that will raise an exception.

    Verify logic to handle DoctestModule.from_parent() raising an exception.
    Note that _pytest.doctest.DoctestModule is not part of the pytest
    public API (not imported by import pytest).
    If a future pytest version changes the function or parameters or
    class the code tested here will show the root cause of the problem.
    """
    monkeypatch.setattr(_pytest.doctest, "DoctestModule", MockDoctestModule())
    pytester.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
    pytester.copy_example("tests/markdown/one_session_block.md")
    rr = pytester.runpytest("-v")
    assert rr.ret == pytest.ExitCode.TESTS_FAILED
    rr.assert_outcomes(failed=1)
    rr.stdout.fnmatch_lines(
        [
            "*::one_session_block.py::test_unable_to_collect_doctests FAILED*",
            "*built from one_session_block.md*",
            "*pytest_phmdoctest.collectors.make_doctest_module() raised*",
            "*Try using --phmdoctest-generate option.*",
        ],
        consecutive=False,
    )


@pytest.mark.skipif(PYTEST_LT_7, reason="n/a pytest <= 7")
def test_bad_doctest_skip_session(pytester, monkeypatch):
    """Inject a DoctestModule that will raise an exception.

    Show that a bad DoctestModule will not cause a problem when
    no sessions are detected.
    """
    monkeypatch.setattr(_pytest.doctest, "DoctestModule", MockDoctestModule())
    pytester.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
    pytester.copy_example("tests/markdown/one_skipped_session.md")
    rr = pytester.runpytest("-v")
    assert rr.ret == pytest.ExitCode.NO_TESTS_COLLECTED
    rr.assert_outcomes()
    rr.stdout.fnmatch_lines(
        [
            "*collected 0 items*",
        ],
        consecutive=True,
    )


@pytest.mark.skipif(PYTEST_LT_7, reason="n/a pytest <= 7")
def test_bad_doctest_skip_session_code_example(pytester, monkeypatch):
    """Inject a DoctestModule that will raise an exception.

    Show that a bad DoctestModule will not cause a problem when
    no sessions are detected and that Python code/expected output
    test cases are collected.
    """
    monkeypatch.setattr(_pytest.doctest, "DoctestModule", MockDoctestModule())
    pytester.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
    pytester.copy_example("tests/markdown/one_python_and_one_skipped_session.md")
    rr = pytester.runpytest("-v")
    assert rr.ret == pytest.ExitCode.OK
    rr.assert_outcomes(passed=1)
    rr.stdout.fnmatch_lines(
        [
            "*one_python_and_one_skipped_session.py::test_code_14_output_18*",
        ],
        consecutive=True,
    )
