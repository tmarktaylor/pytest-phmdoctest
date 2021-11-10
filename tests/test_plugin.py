"""Test cases for pytest plugin pytest-phmdoctest."""
import configparser
from pathlib import Path
import sys

import pytest_phmdoctest
import pytest


# Note- requires conftest.py with    pytest_plugins = ["pytester"]
# Note- Requires pytest >= 6.2


class TestSameVersions:
    """Verify same release version string in all places.

    Obtain the version string from various places in the source tree
    and check that they are all the same.
    Compare all the occurrences to pytest_phmdoctest.__version__.
    This test does not prove the version is correct.
    Whitespace may be significant in some cases.
    """

    package_version = pytest_phmdoctest.__version__

    def verify_found_in_file(self, filename, format_spec="{}"):
        """Format the package version and look for result in caller's file."""
        looking_for = format_spec.format(self.package_version)
        text = Path(filename).read_text(encoding="utf-8")
        assert looking_for in text

    def test_readme_md(self):
        """Check the version near the top of README.md."""
        self.verify_found_in_file("README.md", "# pytest-phmdoctest {}")

    def test_index_rst(self):
        """Check the version is anywhere in index.rst."""
        self.verify_found_in_file("index.rst", "pytest-phmdoctest {}\n=============")

    def test_recent_changes(self):
        """Check the version is anywhere in recent_changes.md."""
        self.verify_found_in_file("doc/recent_changes.md", "{} - ")

    def test_conf_py_release(self):
        """Check version in the release = line in conf.py."""
        self.verify_found_in_file("conf.py", 'release = "{}"')

    def test_setup_cfg(self):
        """Check the version in setup.cfg."""
        config = configparser.ConfigParser()
        config.read("setup.cfg")
        metadata_version = config["metadata"]["version"]
        assert metadata_version == self.package_version


def test_help(pytester):
    """Look for group, addoptions, addini."""
    pytester.makeini("[pytest]\naddopts = --phmdoctest\n")
    rr = pytester.runpytest("--help")
    assert rr.ret == pytest.ExitCode.OK
    rr.stdout.fnmatch_lines(
        [
            "*phmdoctest:*",
            "  --phmdoctest*",
            "  --phmdoctest-save=dir*",
            "*phmdoctest-collect (linelist):*",
        ],
    )


def test_collect_root(pytester):
    """A single file at pytest root is collected and tested."""
    pytester.makeini("[pytest]\naddopts = --phmdoctest\n")
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
    pytester.makeini("[pytest]\naddopts = --phmdoctest\n")
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


def test_plugin_on_command_line(pytester, file_creator):
    """Show pytest loads the plugin when --phmdoctest is on the command line."""
    file_creator.populate_doc(pytester_object=pytester)
    rr = pytester.runpytest("--phmdoctest", "-v", "--ignore", "doc/directive2.md")
    rr.assert_outcomes(passed=5)


def test_pytest_ignore_one(pytester, file_creator):
    """Show that Markdown files can be ignored from the command line."""
    pytester.makeini("[pytest]\naddopts = --phmdoctest\n")
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("-v", "--ignore", "doc/directive2.md")
    rr.assert_outcomes(passed=8)


def test_pytest_ignore_twice(pytester, file_creator):
    """Show that Markdown files can be ignored from the command line."""
    pytester.makeini("[pytest]\naddopts = --phmdoctest\n")
    file_creator.populate_all(pytester_object=pytester)

    rr = pytester.runpytest(
        "-v", "--ignore", "README.md", "--ignore", "doc/directive2.md"
    )
    rr.assert_outcomes(passed=6)
    rr.stdout.fnmatch_lines(
        [
            "*::doc__nocode.py::test_nothing_passes*",
            "*::doc__project.py::doc__project.session_00001_line_31*",
            "*::doc__project.py::doc__project.session_00002_line_46*",
            "*::doc__project.py::doc__project.session_00003_line_55*",
            "*::doc__project.py::test_code_12_output_19*",
            "*tests/test_example.py::test_example*",
        ],
        consecutive=True,
    )


def test_pytest_ignore_glob_wildcard(pytester, file_creator):
    """Show that Markdown files can be ignored from the command line."""
    pytester.makeini("[pytest]\naddopts = --phmdoctest\n")
    file_creator.populate_all(pytester_object=pytester)

    rr = pytester.runpytest("-v", "--ignore-glob", "*/*.md")
    rr.assert_outcomes(passed=3)
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::README.session_00001_line_24*",
            "*::README.py::test_code_10_output_17*",
            "*tests/test_example.py::test_example*",
        ],
        consecutive=True,
    )


def test_collect_specific(pytester, file_creator):
    """Specify single .md file to collect on the command line."""
    pytester.makeini("[pytest]\naddopts = --phmdoctest\n")
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("README.md", "-v")
    assert rr.ret == pytest.ExitCode.OK
    rr.assert_outcomes(passed=2)
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::README.session_00001_line_24*",
            "*::README.py::test_code_10_output_17*",
        ],
        consecutive=True,
    )


def test_collect_specific_no_ini(pytester, file_creator):
    """Specify --phmdoctest and single .md file to collect on the command line."""
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("doc/nocode.md", "--phmdoctest", "-v")
    assert rr.ret == pytest.ExitCode.OK
    rr.assert_outcomes(passed=1)
    rr.stdout.fnmatch_lines(
        [
            "*::doc__nocode.py::test_nothing_passes*",
        ],
        consecutive=True,
    )


def test_failing_doctest_item(pytester, file_creator):
    """Show how a failing doctest is displayed."""

    file_creator.populate_all(pytester_object=pytester)
    contents = Path("README.md").read_text(encoding="utf-8")
    injected = contents.replace("<BLANKLINE>", "<BOGUS>")
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(injected)
    rr = pytester.runpytest("--phmdoctest", "-v")
    rr.assert_outcomes(failed=1, passed=10)
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::README.session_00001_line_24 FAILED*",
            "*::README.py::test_code_10_output_17 PASSED*",
            "*::doc__directive2.py::test_code_25_output_32 PASSED*",
            "*::doc__directive2.py::test_code_42_output_47 PASSED*",
            "*::doc__directive2.py::test_code_52_output_56 PASSED*",
            "*::doc__nocode.py::test_nothing_passes PASSED*",
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

    rr.stdout.fnmatch_lines(
        [
            "*>>> print('Hello*",
            "*Differences (unified diff with -expected +actual):*",
            "*@@ -1,3 +1,3 @@",
            "*Hello",
            "*-<BOGUS>",
            "*+<BLANKLINE>",
            "*World!*",
        ],
        consecutive=True,
    )


def test_failing_python_item(pytester, file_creator):
    """Show how a failing Python snippet is displayed."""

    file_creator.populate_all(pytester_object=pytester)
    contents = Path("tests/test_example.py").read_text(encoding="utf-8")
    injected = contents.replace("coffee = 3", "coffee = 5")
    with open("tests/test_example.py", "w", encoding="utf-8") as f:
        f.write(injected)
    rr = pytester.runpytest("--phmdoctest", "-v")
    rr.assert_outcomes(failed=1, passed=10)
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::README.session_00001_line_24 PASSED*",
            "*::README.py::test_code_10_output_17 PASSED*",
            "*::doc__directive2.py::test_code_25_output_32 PASSED*",
            "*::doc__directive2.py::test_code_42_output_47 PASSED*",
            "*::doc__directive2.py::test_code_52_output_56 PASSED*",
            "*::doc__nocode.py::test_nothing_passes PASSED*",
            "*::doc__project.py::doc__project.session_00001_line_31 PASSED*",
            "*::doc__project.py::doc__project.session_00002_line_46 PASSED*",
            "*::doc__project.py::doc__project.session_00003_line_55 PASSED*",
            "*::doc__project.py::test_code_12_output_19 PASSED*",
            "*tests/test_example.py::test_example FAILED*",
        ],
        consecutive=True,
    )
    # Selected lines from the expected stdout showing the trace and
    # captured stdout from ndiff showing what failed compare_exact.
    rr.stdout.fnmatch_lines(
        [
            "*def test_example():*",
            "*coffee = 5*",
            "*coding = 4*",
            "*assert enjoyment == coffee + coding*",
            "*assert 7 == 9*",
            "*+7",
            "*-9*",
        ],
    )


def test_setup_doctest_scope(pytester):
    """Show the pytest session wide scope of doctest_namespace vars.

    This shows that the fixture doctest_namespace has session scope since
    changes made by one pytest module are seen by another. Whichever module
    runs second will raise AssertionError. There are two pytest runs below
    where the order is swapped.

    The scope is pytest scope="session".  The two pytest files
    - test_setup_doctest1.py
    - test_setup_doctest2.py
    The 2 files have identical code. Each file modifies the doctest_namespace.
    There are 2 populate_doctest_namespace fixtures, one in each file.
    They are both run at pytest session setup time in the order that
    the files are collected by pytest.
    The modification to the samespace made by the first file's tests cause
    the second file's test case to file.
    The order these files are collected are swapped for the second
    runpytest call.  In both cases the second file collected fails
    the test.
    """
    pytester.copy_example("tests/setup_doctest_demo/test_setup_doctest1.py")
    pytester.copy_example("tests/setup_doctest_demo/test_setup_doctest2.py")
    rr = pytester.runpytest(
        "test_setup_doctest1.py",
        "test_setup_doctest2.py",
        "-v",
        "--doctest-modules",
    )
    assert rr.ret == pytest.ExitCode.TESTS_FAILED
    rr.assert_outcomes(passed=11, failed=1)
    rr.stdout.fnmatch_lines(
        [
            "*test_setup_doctest1.py::test_setup_doctest1.session_00000*",
            "*test_setup_doctest1.py::test_setup_doctest1.session_00001_line_69*",
            "*test_setup_doctest1.py::test_setup_doctest1.session_00002_line_76*",
            "*test_setup_doctest1.py::test_code_20_output_27*",
            "*test_setup_doctest1.py::test_code_37_output_42*",
            "*test_setup_doctest1.py::test_code_47_output_51*",
            "*test_setup_doctest2.py::test_setup_doctest2.session_00000 FAILED*",
            "*test_setup_doctest2.py::test_setup_doctest2.session_00001_line_69*",
            "*test_setup_doctest2.py::test_setup_doctest2.session_00002_line_76*",
            "*test_setup_doctest2.py::test_code_20_output_27*",
            "*test_setup_doctest2.py::test_code_37_output_42*",
            "*test_setup_doctest2.py::test_code_47_output_51*",
        ],
        consecutive=True,
    )

    rr2 = pytester.runpytest(
        "test_setup_doctest2.py",
        "test_setup_doctest1.py",
        "-v",
        "--doctest-modules",
    )
    assert rr2.ret == pytest.ExitCode.TESTS_FAILED
    rr2.assert_outcomes(passed=11, failed=1)
    rr2.stdout.fnmatch_lines(
        [
            "*test_setup_doctest2.py::test_setup_doctest2.session_00000*",
            "*test_setup_doctest2.py::test_setup_doctest2.session_00001_line_69*",
            "*test_setup_doctest2.py::test_setup_doctest2.session_00002_line_76*",
            "*test_setup_doctest2.py::test_code_20_output_27*",
            "*test_setup_doctest2.py::test_code_37_output_42*",
            "*test_setup_doctest2.py::test_code_47_output_51*",
            "*test_setup_doctest1.py::test_setup_doctest1.session_00000 FAILED*",
            "*test_setup_doctest1.py::test_setup_doctest1.session_00001_line_69*",
            "*test_setup_doctest1.py::test_setup_doctest1.session_00002_line_76*",
            "*test_setup_doctest1.py::test_code_20_output_27*",
            "*test_setup_doctest1.py::test_code_37_output_42*",
            "*test_setup_doctest1.py::test_code_47_output_51*",
        ],
        consecutive=True,
    )


@pytest.mark.skipif(sys.version_info < (3, 8), reason="requires >=py3.8")
def test_directive1(pytester):
    """Specify single .md file to collect on the command line."""
    pytester.makeini("[pytest]\naddopts = --phmdoctest\n")
    pytester.copy_example("tests/markdown/directive1.md")
    rr = pytester.runpytest("-v")
    assert rr.ret == pytest.ExitCode.OK
    rr.assert_outcomes(passed=3, skipped=1)
    rr.stdout.fnmatch_lines(
        [
            "*::directive1.py::directive1.doctest_print_coffee*",  # this is the doctest
            "*::directive1.py::test_code_23*",
            "*::directive1.py::test_mark_skip SKIPPED (unconditional skip)*",
            "*::directive1.py::test_i_ratio*",
        ],
    )


def test_directive3(pytester):
    """Specify single .md file to collect on the command line."""
    pytester.makeini("[pytest]\naddopts = --phmdoctest\n")
    pytester.copy_example("tests/markdown/directive3.md")
    rr = pytester.runpytest("-v")
    assert rr.ret == pytest.ExitCode.OK
    rr.assert_outcomes(passed=9)
    rr.stdout.fnmatch_lines(
        [
            "*::directive3.py::test_code_13_output_17*",
            "*::directive3.py::test_not_visible*",
            "*::directive3.py::test_directive_share_names*",
            "*::directive3.py::test_code_53_output_60*",
            "*::directive3.py::test_code_70*",
            "*::directive3.py::test_code_75_output_79*",
            "*::directive3.py::test_code_85_output_93*",
            "*::directive3.py::test_code_108_output_114*",
            "*::directive3.py::test_code_121*",
        ],
        consecutive=True,
    )
