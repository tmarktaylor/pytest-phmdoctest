"""Test cases for pytest plugin pytest-phmdoctest."""
import configparser
from pathlib import Path
import sys

import pytest_phmdoctest
import pytest


# Note- requires conftest.py at root with    pytest_plugins = ["pytester"]
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
        self.verify_found_in_file("README.md", "# pytest-phmdoctest {}\n")

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

    def test_sample_pytest_ini(self):
        """Check the version is anywhere in tests/sample/pytest.ini.

        Developers: Please manually verify the numbers of items collected
        by the commands shown in tests/sample/pytest.ini.
        """
        self.verify_found_in_file(
            "tests/sample/pytest.ini", "pytest-phmdoctest version {} is installed."
        )


def test_help(pytester):
    """Look for group, addoptions, addini."""
    rr = pytester.runpytest("--help")
    assert rr.ret == pytest.ExitCode.OK
    rr.stdout.fnmatch_lines(
        [
            "*phmdoctest:*",
            "  --phmdoctest-docmod*",
            "  --phmdoctest-generate=DIR*",
            "*phmdoctest-collect (linelist):*",
        ],
    )


def test_bad_usage(pytester):
    """Try illegal combinations of command line options."""
    expected_usage_lines = [
        "*usage error*phmdoctest, --phmdoctest-generate, --phmdoctest-docmod*",
    ]

    rr = pytester.runpytest("--phmdoctest", "--phmdoctest-docmod")
    assert rr.ret == pytest.ExitCode.USAGE_ERROR
    rr.stderr.fnmatch_lines(expected_usage_lines)

    rr = pytester.runpytest("--phmdoctest-docmod", "--phmdoctest-generate", ".gendir")
    assert rr.ret == pytest.ExitCode.USAGE_ERROR
    print(rr.stderr)
    rr.stderr.fnmatch_lines(expected_usage_lines)

    rr = pytester.runpytest("--phmdoctest-generate", ".gendir", "--phmdoctest")
    assert rr.ret == pytest.ExitCode.USAGE_ERROR
    rr.stderr.fnmatch_lines(expected_usage_lines)

    rr = pytester.runpytest(
        "--phmdoctest", "--phmdoctest-generate", ".gendir" "--phmdoctest-docmod"
    )
    assert rr.ret == pytest.ExitCode.USAGE_ERROR
    rr.stderr.fnmatch_lines(expected_usage_lines)


def test_generate_collect_root(pytester):
    """1. A single file at pytest root is collected and tested... .

    2. Show the generate dir is flushed of pre-existing *.py and prior test_*.py
    files.
    3. Show that a pre-existing *.py file is preserved for later recovery.
    """
    pytester.makeini("[pytest]\naddopts = --phmdoctest-generate .gendir\n")
    pytester.copy_example("tests/sample/README.md")
    rr1 = pytester.runpytest("-v", "README.md", ".gendir")
    assert rr1.ret == pytest.ExitCode.OK
    rr1.assert_outcomes(passed=1)
    rr1.stdout.fnmatch_lines(
        [
            "*.gendir/test_README.py::test_code_10_output_17*",
        ],
        consecutive=True,
    )
    assert Path(".gendir/test_README.py").exists()

    # Show that generated test file from the prior run is overwritten.
    # Do this by replacing the generated test file contents
    # with a single assert statement that will
    # fail as soon as it is imported by pytest.
    assert 13 == Path(".gendir/test_README.py").write_text(
        "assert False\n", encoding="utf-8"
    )

    # Create a pre-existing *.py file in .gendir to show:
    # 1. It is not tested.
    # 2. It is preserved.
    Path(".gendir/test_fails.py").write_text("assert False\n", encoding="utf-8")

    rr2 = pytester.runpytest("-v", "README.md", ".gendir", "--doctest-modules")
    assert rr2.ret == pytest.ExitCode.OK
    rr2.assert_outcomes(passed=2)
    rr2.stdout.fnmatch_lines(
        [
            "*.gendir/test_README.py::test_README.session_00001_line_24*",
            "*.gendir/test_README.py::test_code_10_output_17*",
        ],
        consecutive=True,
    )
    assert Path(".gendir/test_README.py").exists()
    assert Path(".gendir/notest_README.sav").exists()
    assert Path(".gendir/notest_fails.sav").exists()

    # Show that that running again does not disturb the preserved file
    # notest_fails.sav.
    rr3 = pytester.runpytest("-v", "README.md", ".gendir", "--doctest-modules")
    assert rr3.ret == pytest.ExitCode.OK
    rr3.assert_outcomes(passed=2)
    rr3.stdout.fnmatch_lines(
        [
            "*.gendir/test_README.py::test_README.session_00001_line_24*",
            "*.gendir/test_README.py::test_code_10_output_17*",
        ],
        consecutive=True,
    )
    assert Path(".gendir/test_README.py").exists()
    assert Path(".gendir/notest_README.sav").exists()
    assert Path(".gendir/notest_fails.sav").exists()
    assert (
        Path(".gendir/notest_fails.sav").read_text(encoding="utf-8") == "assert False\n"
    )


def test_generate_collect_subdir(pytester):
    """A single file at pytest root/doc is collected and tested."""

    # Note that since we have the argument .gendir on the command line
    # to collect the generated files, we need to explicitly another
    # argument before gen dir to collect the Markdown files.
    pytester.makeini("[pytest]\naddopts = --phmdoctest-generate=.gendir\n")
    pytester.copy_example("tests/sample/doc/directive2.md")
    pytester.mkdir("doc")
    Path("directive2.md").rename("doc/directive2.md")
    rr = pytester.runpytest("-v", "doc", ".gendir")
    rr.assert_outcomes(passed=3)
    rr.stdout.fnmatch_lines(
        [
            "*.gendir/test_doc__directive2.py::test_code_25_output_32*",
            "*.gendir/test_doc__directive2.py::test_code_42_output_47*",
            "*.gendir/test_doc__directive2.py::test_code_52_output_56*",
        ],
        consecutive=True,
    )


def test_plugin_on_command_line(pytester, file_creator):
    """Show pytest loads the plugin when --phmdoctest is on the command line."""
    file_creator.populate_doc(pytester_object=pytester)
    rr = pytester.runpytest(
        "--phmdoctest-docmod", "-v", "--ignore", "doc/directive2.md"
    )
    rr.assert_outcomes(passed=4)


def test_pytest_ignore_one(pytester, file_creator):
    """Show that Markdown files can be ignored from the command line."""
    pytester.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("-v", "--ignore", "doc/directive2.md")
    rr.assert_outcomes(passed=7)


def test_pytest_ignore_twice(pytester, file_creator):
    """Show that Markdown files can be ignored from the command line."""
    pytester.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
    file_creator.populate_all(pytester_object=pytester)

    rr = pytester.runpytest(
        "-v", "--ignore", "README.md", "--ignore", "doc/directive2.md"
    )
    rr.assert_outcomes(passed=5)
    rr.stdout.fnmatch_lines(
        [
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
    pytester.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
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


def test_collect_no_python_blocks(pytester, file_creator):
    """Specify single .md file that has no Python blocks on the command line."""
    pytester.makeini("[pytest]\naddopts = --phmdoctest-generate .gendir\n")
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("-v", "CONTRIBUTING.md")
    assert rr.ret == pytest.ExitCode.NO_TESTS_COLLECTED


def test_collect_specific(pytester, file_creator):
    """Specify single .md file to collect on the command line."""
    pytester.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
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
    rr = pytester.runpytest("doc/project.md", "--phmdoctest-docmod", "-v")
    assert rr.ret == pytest.ExitCode.OK
    rr.assert_outcomes(passed=4)
    rr.stdout.fnmatch_lines(
        [
            "*::doc__project.py::doc__project.session_00001_line_31 PASSED*",
            "*::doc__project.py::doc__project.session_00002_line_46 PASSED*",
            "*::doc__project.py::doc__project.session_00003_line_55 PASSED*",
            "*::doc__project.py::test_code_12_output_19 PASSED*",
        ],
        consecutive=True,
    )


def test_failing_doctest_item(pytester, file_creator):
    """Show a generated failing doctest."""

    file_creator.populate_all(pytester_object=pytester)
    contents = Path("README.md").read_text(encoding="utf-8")
    injected = contents.replace("<BLANKLINE>", "<BOGUS>")
    _ = Path("README.md").write_text(injected, encoding="utf-8")
    rr = pytester.runpytest("--phmdoctest-docmod", "-v")
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


def test_failing_python_item(pytester, file_creator):
    """Show a generated failing Python code example."""

    file_creator.populate_all(pytester_object=pytester)
    contents = Path("doc/directive2.md").read_text(encoding="utf-8")
    injected = contents.replace("== [1, 2, 3, 4]", "== [1, 2, 3, 4, 9999]")
    _ = Path("doc/directive2.md").write_text(injected, encoding="utf-8")
    rr = pytester.runpytest("--phmdoctest-docmod", "-v")
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
    pytester.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
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
    pytester.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
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


def test_one_python_block(pytester):
    """Collect a .md file that has just one Python code block.

    Show phmdoctest.tool.detect_python_examples() can detect a python block.
    """
    pytester.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
    pytester.copy_example("tests/markdown/one_python_block.md")
    rr = pytester.runpytest("-v")
    assert rr.ret == pytest.ExitCode.OK
    rr.assert_outcomes(passed=1)
    rr.stdout.fnmatch_lines(
        [
            "*::one_python_block.py::test_code_7_output_14*",
        ],
        consecutive=True,
    )


def test_one_session_block(pytester):
    """Collect a .md file that has just one interactive session block.

    Show phmdoctest.tool.detect_python_examples() can detect a session block.
    """
    pytester.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
    pytester.copy_example("tests/markdown/one_session_block.md")
    rr = pytester.runpytest("-v")
    assert rr.ret == pytest.ExitCode.OK
    rr.assert_outcomes(passed=1)
    rr.stdout.fnmatch_lines(
        [
            "*::one_session_block.py::one_session_block.session_00001_line_8*",
        ],
        consecutive=True,
    )


def test_file_has_no_examples(pytester):
    """Collect a .md file that has no code or interactive session blocks."""
    pytester.makeini("[pytest]\naddopts = --phmdoctest-docmod\n")
    pytester.copy_example("CONTRIBUTING.md")
    rr = pytester.runpytest("-v")
    assert rr.ret == pytest.ExitCode.NO_TESTS_COLLECTED
    rr.assert_outcomes()
    rr.stdout.fnmatch_lines(
        [
            "*collected 0 items*",
        ],
        consecutive=True,
    )
