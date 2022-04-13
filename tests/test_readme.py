"""Test cases for pytest plugin pytest-phmdoctest README.md docs."""
import inspect
from packaging.version import Version
from pathlib import Path
import re
import subprocess
import sys
from typing import List

import _pytest.doctest

import phmdoctest.tool
import pytest_phmdoctest
import pytest_phmdoctest.collectors
import pytest


labeled_fcbs = phmdoctest.tool.FCBChooser("README.md")


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires >=py3.7")
def test_trailing_whitespace():
    """Expose files in repository that have lines with trailing spaces.

    Note- The IDE and/or git may be configurable to prevent trailing spaces
    making this test redundant.
    To run just this test: pytest -v tests -k test_trailing_whitespace
    """
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        ["git", "ls-files"], text=True, capture_output=True
    )
    files: List[str] = completed.stdout.splitlines()
    found_trailing_spaces = False
    for name in files:
        contents = Path(name).read_text(encoding="utf-8")
        lines = contents.splitlines()
        for num, got in enumerate(lines, start=1):
            wanted = got.rstrip()
            if got != wanted:
                if not found_trailing_spaces:
                    print()
                print(name, "line", num, "has trailing whitespace.")
                found_trailing_spaces = True
    assert not found_trailing_spaces, "Line has trailing whitespace."


def make_pytest_command(code: str) -> str:
    """Return a pytest command line built from pytester.runpytest statement.

    The result is a single line as if it were typed in a console.
    This is used to check the contents of a fenced code block in the docs.
    """
    args_pattern = r"pytester.runpytest\((.*?)\)"
    match = re.search(pattern=args_pattern, string=code, flags=re.DOTALL)
    runpytest_args = match.group(1)
    # remove any lines with comments
    args_less_comments = re.sub(r"#.*?$", "", runpytest_args, flags=re.MULTILINE)
    # collapse whitespace including newlines to single space
    collapsed = re.sub(r"\s+", " ", args_less_comments)
    dequote_pattern = r'[^"]*"([^"]*)"'
    dequoted_args = re.findall(pattern=dequote_pattern, string=collapsed)
    return "pytest " + " ".join(dequoted_args)


def collected_items(code: str) -> List[str]:
    """Extract passing and failing items from fnmatch_lines() call in code."""
    # remove any lines with comments
    code_less_comments = re.sub(r"#.*?$", "", code, flags=re.MULTILINE)
    pattern = r'"[*](.* PASSED|.* FAILED)[*]"'
    return re.findall(pattern=pattern, string=code_less_comments)


def make_test_session(num_collected: int, expected_items: List[str]) -> str:
    """Return multi-line string expected value of a test session.

    This is used to check the contents of a fenced code block in the docs.
    """
    version = pytest_phmdoctest.__version__
    lines = [f"plugins: phmdoctest-{version}"]
    if num_collected == 1:
        lines.append(f"collected {num_collected} item")
    else:
        lines.append(f"collected {num_collected} items")
    lines.append("")
    lines.extend(expected_items)
    # Add the newline since fenced code blocks end with newline.
    lines.append("")
    return "\n".join(lines)


def test_introduction_example(pytester, checker):
    """Test README.md introduction examples and expected pytest output.

    Run the plugin on the repository root README.md with pytester using the
    pytest options from the fenced code block.
    Assure the README.md pytest example output is accurate by checking
    the pytester RunResult from stdout against the fenced code block.
    """
    pytester.copy_example("README.md")
    assert Path("README.md").exists()
    blocks = phmdoctest.tool.fenced_code_blocks("README.md")
    # Not using FCBChooser here so this part of README.md has no
    # phmdoctest directives.  The fenced_code_blocks() returns a list of
    # blocks so indexing is needed. This will break if any fenced code blocks
    # are added to or removed from README.md before the first few blocks.
    command = blocks[2]
    introduction_output = blocks[3]
    assert command.startswith("pytest ")
    command2 = command.replace("pytest ", "")
    command3 = command2.rstrip()
    options = command3.split(" ")
    rr = pytester.runpytest(*options)
    rr.assert_outcomes(passed=1)
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::test_code_12_output_16 PASSED*",
        ],
        consecutive=True,
    )
    src = inspect.getsource(test_introduction_example)
    items = collected_items(src)
    num_collected = 1
    assert len(items) == num_collected
    want = make_test_session(num_collected, items)
    checker(want, introduction_output)

    m = re.search(pattern=r"test_code_(..)_output_(..)", string=introduction_output)
    code_line = m.group(1)
    output_line = m.group(2)
    text = Path("README.md").read_text(encoding="utf-8")
    assert f"`test_code_{code_line}_output_{output_line}`" in text
    assert f"`{code_line}`" in text
    assert f"`{output_line}`" in text


def test_plugin_inactive(pytester, file_creator):
    """Collect no .md files since no --phmdoctest.  Collect the .py."""

    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("-v")
    rr.assert_outcomes(passed=1)
    rr.stdout.fnmatch_lines(
        [
            "*tests/test_example.py::test_example PASSED*",
        ],
        consecutive=True,
    )


def test_plugin_inactive_example(checker):
    """Test README.md plugin inactive example.

    The example should contain some of the output captured by pytester.
    Assure the example in README.md is accurate by checking the results
    in stdout that the pytester test case produced.

    We assume that test_plugin_inactive() passes and use the expected
    stdout provided to RunResult.stdout.fnmatch_lines().
    """
    src = inspect.getsource(test_plugin_inactive)
    want1 = make_pytest_command(src)
    got1 = labeled_fcbs.contents(label="plugin-inactive-command")
    checker(want1, got1)
    num_collected = 1
    items = collected_items(src)
    assert len(items) == num_collected
    want2 = make_test_session(num_collected, items)
    got2 = labeled_fcbs.contents(label="plugin-inactive-output")
    checker(want2, got2)


def test_phmdoctest_option(pytester, file_creator):
    """Test the --phmdoctest option."""

    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest(
        "-v",
        "--phmdoctest",
    )
    rr.assert_outcomes(passed=6)
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::test_code_10_output_17 PASSED*",
            "*::doc__directive2.py::test_code_25_output_32 PASSED*",
            "*::doc__directive2.py::test_code_42_output_47 PASSED*",
            "*::doc__directive2.py::test_code_52_output_56 PASSED*",
            "*::doc__project.py::test_code_12_output_19 PASSED*",
            "*tests/test_example.py::test_example PASSED*",
        ],
        consecutive=True,
    )


def test_phmdoctest_option_example(checker):
    """Test the --phmdoctest example in README.md.

    Assure the example in README.md is accurate by checking the results
    in stdout that the pytester test case produced.
    The example should contain some of the output captured by pytester.

    We assume that test_phmdoctest_option() passes and use the expected
    stdout provided to RunResult.stdout.fnmatch_lines().
    """
    src = inspect.getsource(test_phmdoctest_option)
    want1 = make_pytest_command(src)
    got1 = labeled_fcbs.contents(label="phmdoctest-option-command")
    checker(want1, got1)
    num_collected = 6
    items = collected_items(src)
    assert len(items) == num_collected
    want2 = make_test_session(num_collected, items)
    got2 = labeled_fcbs.contents(label="phmdoctest-option-output")
    checker(want2, got2)


def test_phmdoctest_docmod(pytester, file_creator):
    """Test the --phmdoctest-docmod option."""

    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest(
        "-v",
        "--phmdoctest-docmod",
    )
    rr.assert_outcomes(passed=10)
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::README.session_00001_line_24 PASSED*",
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


def test_phmdoctest_docmod_example(checker):
    """Test the --phmdoctest-docmod example in README.md.

    Assure the example in README.md is accurate by checking the results
    in stdout that the pytester test case produced.
    The example should contain some of the output captured by pytester.

    We assume that test_phmdoctest_docmod() passes and use the expected
    stdout provided to RunResult.stdout.fnmatch_lines().
    """
    src = inspect.getsource(test_phmdoctest_docmod)
    want1 = make_pytest_command(src)
    got1 = labeled_fcbs.contents(label="phmdoctest-docmod-command")
    checker(want1, got1)
    num_collected = 10
    items = collected_items(src)
    assert len(items) == num_collected
    want2 = make_test_session(num_collected, items)
    got2 = labeled_fcbs.contents(label="phmdoctest-docmod-output")
    checker(want2, got2)


pytest_version = Version(pytest.__version__)
PYTEST_LT_7 = pytest_version < Version("7.0")


class DemoMockDoctestModule:
    """Method from_parent takes 1 more arg than caller expects.

    Manually observed it cause pytest ExitCode.INTERRUPTED.
    This implies that args/parameter mismatch raised TypeError.
    If caller calls with correct args, return an unuseable object.
    """

    def from_parent(self, parent, path, extra_arg):
        return 99


@pytest.mark.skipif(PYTEST_LT_7, reason="n/a pytest < 7")
def test_broken_doctest_module(pytester, file_creator, monkeypatch):
    """Inject a DoctestModule that will raise an exception.

    Verify logic to handle DoctestModule.from_parent() raising an exception.
    Note that _pytest.doctest.DoctestModule is not part of the pytest
    public API (not imported by import pytest).
    If a future pytest version changes the function or parameters or
    class the code tested here will show the root cause of the problem.
    """
    monkeypatch.setattr(_pytest.doctest, "DoctestModule", DemoMockDoctestModule())

    # pytester.copy_example("tests/markdown/one_session_block.md")
    # Show that non-doctests are still run
    # pytester.copy_example("tests/sample/README.md")

    file_creator.populate_all(pytester_object=pytester)

    rr = pytester.runpytest("-v", "--phmdoctest-docmod")
    assert rr.ret == pytest.ExitCode.TESTS_FAILED
    rr.assert_outcomes(passed=6, failed=2)
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::test_code_10_output_17 PASSED*",
            "*::README.py::test_unable_to_collect_doctests FAILED*",
            "*::doc__directive2.py::test_code_25_output_32 PASSED*",
            "*::doc__directive2.py::test_code_42_output_47 PASSED*",
            "*::doc__directive2.py::test_code_52_output_56 PASSED*",
            "*::doc__project.py::test_code_12_output_19 PASSED*",
            "*::doc__project.py::test_unable_to_collect_doctests FAILED*",
            "*tests/test_example.py::test_example PASSED*",
        ],
        consecutive=False,
    )


@pytest.mark.skipif(PYTEST_LT_7, reason="n/a pytest < 7")
def test_broken_doctest_module_example(checker):
    """Test the --phmdoctest-generate and collect example in README.md.

    Assure the example in README.md is accurate by checking the results
    in stdout that the pytester test case produced.
    The example should contain some of the output captured by pytester.

    We assume that test_broken_doctest_module() passes and use the expected
    stdout provided to RunResult.stdout.fnmatch_lines().
    """
    src = inspect.getsource(test_broken_doctest_module)
    want1 = make_pytest_command(src)
    got1 = labeled_fcbs.contents(label="phmdoctest-bad-api-command")
    checker(want1, got1)
    num_collected = 8
    items = collected_items(src)
    assert len(items) == num_collected
    want2 = make_test_session(num_collected, items)
    got2 = labeled_fcbs.contents(label="phmdoctest-bad-api-output")
    checker(want2, got2)


expected_gendir = ["test_doc__directive2.py", "test_doc__project.py", "test_README.py"]


def test_phmdoctest_generate(pytester, file_creator):
    """Test the --phmdoctest-generate option."""

    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest(
        "-v",
        "--phmdoctest-generate",
        ".gendir",
    )
    rr.assert_outcomes(passed=1)
    rr.stdout.fnmatch_lines(
        [
            "*tests/test_example.py::test_example PASSED*",
        ],
        consecutive=True,
    )
    gendir_contents = [p.name for p in Path(".gendir").glob("*.*")]
    # Comparison is not dependent on glob order which could differ by OS.
    sorted_gendir_contents = sorted(gendir_contents)
    sorted_expected_gendir = sorted(expected_gendir)
    assert sorted_expected_gendir == sorted_gendir_contents


def test_phmdoctest_generate_example(checker):
    """Test the --phmdoctest-generate and collect example in README.md.

    Assure the example in README.md is accurate by checking the results
    in stdout that the pytester test case produced.
    The example should contain some of the output captured by pytester.

    We assume that test_phmdoctest_generate() passes and use the expected
    stdout provided to RunResult.stdout.fnmatch_lines().
    """
    src = inspect.getsource(test_phmdoctest_generate)
    want1 = make_pytest_command(src)
    got1 = labeled_fcbs.contents(label="phmdoctest-generate-command")
    checker(want1, got1)

    num_collected = 1
    items = collected_items(src)
    assert len(items) == num_collected
    want2 = make_test_session(num_collected, items)
    got2 = labeled_fcbs.contents(label="phmdoctest-generate-output")
    checker(want2, got2)

    got3 = labeled_fcbs.contents(label="gendir-files")
    checker("\n".join(expected_gendir), got3)


def test_phmdoctest_generate_and_collect(pytester, file_creator):
    """Test the --phmdoctest-generate and collect."""

    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest(
        "-v",
        "--phmdoctest-generate",
        ".gendir",
        ".",
        ".gendir",
        "--doctest-modules",
        "--ignore",
        "src",
    )
    assert Path(".gendir").exists()
    rr.assert_outcomes(passed=10)
    rr.stdout.fnmatch_lines(
        [
            "*tests/test_example.py::test_example PASSED*",
            "*.gendir/test_README.py::test_README.session_00001_line_24 PASSED*",
            "*.gendir/test_README.py::test_code_10_output_17 PASSED*",
            "*.gendir/test_doc__directive2.py::test_code_25_output_32 PASSED*",
            "*.gendir/test_doc__directive2.py::test_code_42_output_47 PASSED*",
            "*.gendir/test_doc__directive2.py::test_code_52_output_56 PASSED*",
            "*.gendir/test_doc__project.py::test_doc__project.session_00001_line_31 PASSED*",
            "*.gendir/test_doc__project.py::test_doc__project.session_00002_line_46 PASSED*",
            "*.gendir/test_doc__project.py::test_doc__project.session_00003_line_55 PASSED*",
            "*.gendir/test_doc__project.py::test_code_12_output_19 PASSED*",
        ],
        consecutive=True,
    )


def test_phmdoctest_generate_and_collect_example(checker):
    """Test the --phmdoctest-generate and collect example in README.md.

    Assure the example in README.md is accurate by checking the results
    in stdout that the pytester test case produced.
    The example should contain some of the output captured by pytester.

    We assume that test_phmdoctest_generate() passes and use the expected
    stdout provided to RunResult.stdout.fnmatch_lines().
    """
    src = inspect.getsource(test_phmdoctest_generate_and_collect)
    want1 = make_pytest_command(src)
    got1 = labeled_fcbs.contents(label="generate-collect-command")
    checker(want1, got1)
    num_collected = 10
    items = collected_items(src)
    assert len(items) == num_collected
    want2 = make_test_session(num_collected, items)
    got2 = labeled_fcbs.contents(label="generate-collect-output")
    checker(want2, got2)


def test_collect_section(pytester, file_creator):
    """Try phmdoctest-collect glob + options in Collect section."""

    pytester.makefile(
        ".ini",
        pytest="""
        [pytest]
        addopts = --phmdoctest-docmod
        phmdoctest-collect =
            doc/project.md --skip greeting --skip enjoyment
            **/*.md
        """,
    )
    assert Path("pytest.ini").exists()
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("-v", "--ignore", "tests/test_example.py")
    rr.assert_outcomes(passed=7, failed=0)
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::README.session_00001_line_24 PASSED*",
            "*::README.py::test_code_10_output_17 PASSED*",
            "*::doc__directive2.py::test_code_25_output_32 PASSED*",
            "*::doc__directive2.py::test_code_42_output_47 PASSED*",
            "*::doc__directive2.py::test_code_52_output_56 PASSED*",
            "*::doc__project.py::doc__project.session_00001_line_31 PASSED*",
            "*::doc__project.py::doc__project.session_00002_line_46 PASSED*",
        ],
        consecutive=True,
    )


def test_collect_section_example(checker):
    """Test README.md collect section example."""
    src = inspect.getsource(test_collect_section)
    want1 = make_pytest_command(src)
    got1 = labeled_fcbs.contents(label="collect-section-command")
    checker(want1, got1)
    num_collected = 7
    items = collected_items(src)
    print(items)
    assert len(items) == num_collected
    want2 = make_test_session(num_collected, items)
    got2 = labeled_fcbs.contents(label="collect-section-output")
    checker(want2, got2)


def test_quick_links():
    """Make sure the README.md quick links are up to date."""
    filename = "README.md"
    readme = Path(filename).read_text(encoding="utf-8")
    quick_links = make_quick_links(Path(filename))
    # There must be at least one blank line after the last link.
    assert quick_links + "\n\n" in readme


def make_label(title):
    """Make the [] part of a link.  Rewrite if last word is 'option'."""
    # Special handling if the last word of the title is option.
    # The word option indicates the preceding word should have the
    # prefix '--' in the link label since it is a command line option.
    # Titles with '--' seem to break on GitHub pages.
    parts = title.split()
    if parts[-1] == "option":
        parts.pop(-1)
        parts[-1] = "--" + parts[-1]
    title = " ".join(parts)
    return "[" + title + "]"


def make_quick_links(filename: Path):
    """Generate links for a quick links section."""
    header_level = "## "  # note trailing space
    text = filename.read_text(encoding="utf-8")
    lines = [line.rstrip() for line in text.splitlines()]  # lose newlines
    links = []
    for line in lines:
        if line.startswith(header_level):
            assert "--" not in line, "Please rewrite to avert breakage on Pages."
            title = line.replace(header_level, "")
            label = make_label(title)
            link = title.lower()
            link = link.replace(" ", "-")
            link = "(#" + link + ")"
            links.append(label + link)
    return " |\n".join(links)


if __name__ == "__main__":
    """Generate quick links for README.md, check copyrights, check encoding."""
    import datetime

    # To generate quick links, from repository root run: python tests/test_readme.py
    text = make_quick_links(Path("README.md"))
    print(text)
    print()
    num_links = text.count("\n") + 1
    print("created {} links, {} characters".format(num_links, len(text)))

    today = datetime.date.today()
    year_string = f"2021-{today.year}"
    print()
    print(f"\nchecking copyright year is {year_string} ...")
    text1 = Path("conf.py").read_text()
    assert year_string in text1, "conf.py copyright must have current year."
    text2 = Path("LICENSE.txt").read_text()
    assert year_string in text2, "LICENSE.txt copyright must have current year."
    print("copyrights are OK.")

    print("\nChecking for non-ascii characters in repos files...")
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        ["git", "ls-files"], text=True, capture_output=True
    )
    files: List[str] = completed.stdout.splitlines()
    for name in files:
        try:
            _ = Path(name).read_text()  # no encoding
        except UnicodeDecodeError:
            print(
                f'UnicodeDecodeError in "{name}".'
                f' Use Path("{name}").read_text() to duplicate\n'
            )
            raise
    print("repos files are OK.")
