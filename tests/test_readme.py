"""Test cases for pytest plugin pytest-phmdoctest README.md docs."""
from pathlib import Path
import re
import subprocess
import sys
from typing import List

import inspect
import phmdoctest.tool
import pytest_phmdoctest
import pytest


labeled_fcbs = phmdoctest.tool.FCBChooser("README.md")


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires >=py3.7")
def test_trailing_whitespace():
    """Expose files in repository that have lines with trailing spaces.

    Note- The IDE and/or git may be configurable to prevent trailing spaces
    making this test redundant.
    To run just this test: pytest -v tests -k test_trailing_whitespace
    """
    completed = subprocess.run(["git", "ls-files"], text=True, capture_output=True)
    files: List[str] = completed.stdout.splitlines()
    found_trailing_spaces = False
    for name in files:
        text = Path(name).read_text(encoding="utf-8")
        lines = text.splitlines()
        for num, got in enumerate(lines, start=1):
            wanted = got.rstrip()
            if got != wanted:
                print(name, "line", num, "has trailing whitespace.")
                found_trailing_spaces = True
    assert not found_trailing_spaces, "Line has trailing whitespace."


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


def test_collect_all(pytester, file_creator):
    """Collect all the .md files."""

    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("--phmdoctest", "-v")
    rr.assert_outcomes(passed=11)
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
            "*tests/test_example.py::test_example PASSED*",
        ],
        consecutive=True,
    )


def test_collect_nodeid(pytester, file_creator):
    """Collect a generated test file by nodeid."""

    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("--phmdoctest", "-v", "-k", "README.py")
    rr.assert_outcomes(passed=2)
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::README.session_00001_line_24 PASSED*",
            "*::README.py::test_code_10_output_17 PASSED*",
        ],
        consecutive=True,
    )


def make_pytest_command(code: str) -> str:
    """Return a pytest command line built from pytester.runpytest statement.

    This is used to check the contents of a fenced code block in the docs.
    """
    pytest_args_pattern = r"pytester.runpytest\((.*?)\)"
    match = re.search(pattern=pytest_args_pattern, string=code, flags=re.DOTALL)
    args_part = re.sub(r"\s+", " ", match.group(1))
    dequote_pattern = r'[^"]*"([^"]*)"'
    dequoted_args = re.findall(pattern=dequote_pattern, string=args_part)
    return "pytest " + " ".join(dequoted_args)


def collected_items(code: str) -> List[str]:
    """Extract passing and failing items from fnmatch_lines() call in code."""
    pattern = r'"[*](.* PASSED|.* FAILED)[*]"'
    return re.findall(pattern=pattern, string=code)


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
    pytest options from the labeled fenced code block.
    Assure the README.md pytest example output is accurate by checking
    the pytester RunResult from stdout against the labeled fenced code block.
    """
    pytester.copy_example("README.md")
    assert Path("README.md").exists()
    blocks = phmdoctest.tool.fenced_code_blocks("README.md")
    # Not using FCBChooser here so this part of README.md has no
    # phmdoctest directives.  The fenced_code_blocks() returns a list of
    # blocks so indexing is needed. This will break if any fenced code blocks
    # are added to or removed from README.md before the first few blocks.
    command = blocks[3]
    introduction_output = blocks[4]
    assert command.startswith("pytest ")
    command2 = command.replace("pytest ", "")
    command3 = command2.rstrip()
    options = command3.split(" ")
    rr = pytester.runpytest(*options)
    rr.assert_outcomes(passed=2)
    rr.stdout.fnmatch_lines(
        [
            "*::README.py::README.session_00001_line_24 PASSED*",
            "*::README.py::test_code_14_output_18 PASSED*",
        ],
        consecutive=True,
    )
    src = inspect.getsource(test_introduction_example)
    items = collected_items(src)
    num_collected = 2
    assert len(items) == num_collected
    want = make_test_session(num_collected, items)
    checker(want, introduction_output)


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


def test_collect_all_example(checker):
    """Test README.md collect all example.

    Assure the example in README.md is accurate by checking the results
    in stdout that the pytester test case produced.
    The example should contain some of the output captured by pytester.

    We assume that test_collect_all() passes and use the expected
    stdout provided to RunResult.stdout.fnmatch_lines().
    """
    src = inspect.getsource(test_collect_all)
    want1 = make_pytest_command(src)
    got1 = labeled_fcbs.contents(label="plugin-enabled-command")
    checker(want1, got1)
    num_collected = 11
    items = collected_items(src)
    assert len(items) == num_collected
    want2 = make_test_session(num_collected, items)
    got2 = labeled_fcbs.contents(label="plugin-enabled-output")
    checker(want2, got2)


def test_collect_fail_nocode(pytester, file_creator):
    """Collect section with a --fail-nocode arg."""

    pytester.makefile(
        ".ini",
        pytest="""
        [pytest]
        addopts = --phmdoctest
        phmdoctest-collect =
            doc/project.md
            **/*code.md --fail-nocode
        """,
    )
    assert Path("pytest.ini").exists()
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("-v", "--ignore", "tests/test_example.py")
    rr.assert_outcomes(passed=4, failed=1)
    rr.stdout.fnmatch_lines(
        [
            "*::doc__nocode.py::test_nothing_fails FAILED*",
            "*::doc__project.py::doc__project.session_00001_line_31 PASSED*",
            "*::doc__project.py::doc__project.session_00002_line_46 PASSED*",
            "*::doc__project.py::doc__project.session_00003_line_55 PASSED*",
            "*::doc__project.py::test_code_12_output_19 PASSED*",
        ],
        consecutive=True,
    )


def test_collect_fail_nocode_example(checker):
    """Test README.md collect section example."""
    src = inspect.getsource(test_collect_fail_nocode)
    want1 = make_pytest_command(src)
    got1 = labeled_fcbs.contents(label="collect-section-command")
    checker(want1, got1)
    num_collected = 5
    items = collected_items(src)
    print(items)
    assert len(items) == num_collected
    want2 = make_test_session(num_collected, items)
    got2 = labeled_fcbs.contents(label="collect-section-output")
    checker(want2, got2)


def test_quick_links():
    """Make sure the README.md quick links are up to date."""
    filename = "README.md"
    readme = Path("README.md").read_text(encoding="utf-8")
    quick_links = make_quick_links(filename)
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


def make_quick_links(filename):
    """Generate links for a quick links section."""
    header_level = "## "  # note trailing space
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
    lines = [line.rstrip() for line in lines]  # lose newlines
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
    # To generate quick links, from repository root run: python tests/test_readme.py
    text = make_quick_links("README.md")
    print(text)
    print()
    num_links = text.count("\n") + 1
    print("created {} links, {} characters".format(num_links, len(text)))
