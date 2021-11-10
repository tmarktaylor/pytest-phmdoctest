"""Test cases for make_collect_parser() and parse_collect_line()."""
import re

import pytest

from pytest_phmdoctest.plugin import make_collect_parser
from pytest_phmdoctest.plugin import parse_collect_line

parser = make_collect_parser()


def test_parseble():
    """Assure the line parses without error.  Does not check the result values."""
    lines = [
        "doc/*.md --skip Floats --setup MyTEXT --setup-doctest --fail-nocode --teardown=Hi",
        'doc/*.md --skip Floats --setup MyTEXT --setup-doctest --fail-nocode --teardown="Hi"',
        'doc/*.md --skip Floats --setup MyTEXT --setup-doctest --fail-nocode --teardown "Hi"',
        'doc/*.md --skip="Very small rocks" --setup=MyTEXT --setup-doctest --fail-nocode',
        "doc/*.md --skip=Floats --skip CIDER --setup=MyTEXT --setup-doctest --fail-nocode",
        'doc/*.md --skip=Floats --skip "CIDER" --setup=MyTEXT --setup-doctest --fail-nocode',
        "doc/*.md --skip=Floats -sCIDER --setup=MyTEXT --setup-doctest --fail-nocode",
        'doc/*.md --skip=Floats" --setup=MyTEXT --setup-doctest --fail-nocode',
        'doc/*.md --skip=Floats --skip "CIDER" -u=MyTEXT -d"tear me down" --fail-nocode',
        'spec -u"My TEXT"',
        'spec -d"My TEXT"',
        'spec -s "appl es" --fail-nocode',
        'file -d "Very small rocks" -s"CIDER" -s"appl es" -uMyTEXT --fail-nocode',
        'doc/*.md --skip="Very small rocks" -sCIDER --setup=MyTEXT --setup-doctest --fail-nocode',
        'doc/*.md --skip="Very small rocks" --skip "CIDER" -uMyTEXT -d"tear me down" --fail-nocode',
    ]
    for line in lines:
        args = parse_collect_line(parser, line)
        assert len(args) == 6


def test_typical_line():
    """Check parsed arguments for a typical input line."""
    line = "doc/*.md --skip Floats --setup MyTEXT --setup-doctest"
    args = parse_collect_line(parser, line)
    assert args == {
        "file_glob": "doc/*.md",
        "skips": ["Floats"],
        "fail_nocode": None,
        "setup": "MyTEXT",
        "teardown": None,
        "setup_doctest": True,
    }


def test_quoted_skip():
    """Check parsed arguments with quoted --skip value."""
    line = 'doc/*.md --skip "Very small rocks" --setup MyTEXT --setup-doctest --fail-nocode'
    args = parse_collect_line(parser, line)
    assert args == {
        "file_glob": "doc/*.md",
        "skips": ["Very small rocks"],
        "fail_nocode": True,
        "setup": "MyTEXT",
        "teardown": None,
        "setup_doctest": True,
    }


def test_all_arguments():
    """Check parsed arguments with all options specified."""
    line = 'doc/*.md --skip "Floats" -s Cherries --setup MyTEXT --teardown CIDER --setup-doctest --fail-nocode'
    args = parse_collect_line(parser, line)
    assert args == {
        "file_glob": "doc/*.md",
        "skips": ["Floats", "Cherries"],
        "fail_nocode": True,
        "setup": "MyTEXT",
        "teardown": "CIDER",
        "setup_doctest": True,
    }


def test_equals_forms():
    """Check parsed arguments with option=value form."""
    line = 'doc/*.md --skip="Floats" -s=Cherries --setup=MyTEXT --teardown=CIDER --setup-doctest --fail-nocode'
    args = parse_collect_line(parser, line)
    assert args == {
        "file_glob": "doc/*.md",
        "skips": ["Floats", "Cherries"],
        "fail_nocode": True,
        "setup": "MyTEXT",
        "teardown": "CIDER",
        "setup_doctest": True,
    }


def test_short_forms():
    """Check parsed arguments with one character options."""
    line = 'doc/*.md --skip="Floats" -sCherries -uMyTEXT -dCIDER --setup-doctest --fail-nocode'
    args = parse_collect_line(parser, line)
    assert args == {
        "file_glob": "doc/*.md",
        "skips": ["Floats", "Cherries"],
        "fail_nocode": True,
        "setup": "MyTEXT",
        "teardown": "CIDER",
        "setup_doctest": True,
    }


def test_short_equals_forms():
    """Check parsed arguments with one character options with =value."""
    line = 'doc/*.md --skip="Floats" -s=Cherries -u=MyTEXT -d=CIDER --setup-doctest --fail-nocode'
    args = parse_collect_line(parser, line)
    assert args == {
        "file_glob": "doc/*.md",
        "skips": ["Floats", "Cherries"],
        "fail_nocode": True,
        "setup": "MyTEXT",
        "teardown": "CIDER",
        "setup_doctest": True,
    }


def test_quoted_short_forms():
    """Check parsed arguments short options with quoted value."""
    line = 'doc/*.md --skip="Floats" -s"Cher ries" -u"My TEXT" -d"CI DER" --setup-doctest --fail-nocode'
    args = parse_collect_line(parser, line)
    assert args == {
        "file_glob": "doc/*.md",
        "skips": ["Floats", "Cher ries"],
        "fail_nocode": True,
        "setup": "My TEXT",
        "teardown": "CI DER",
        "setup_doctest": True,
    }


def test_bad_argument():
    """Ini line parsing error returns {"ini-error": error_text}.

    Caution- This test depends somewhat on formatting done by
    argparse.ArgumentParser which may change in future Python versions.
    The tests below collapse runs of whitespace to 1 space to
    prevent failing on whitespace differences.
    """
    line = "myglob --bogus --skip Floats --setup MyTEXT --setup-doctest"
    parsed = parse_collect_line(parser, line)
    assert len(parsed) == 1  # 1 item in the dict
    assert "ini-error" in parsed
    expected_lines1 = [
        "pytest-phmdoctest parse error on the following line:",
        "myglob --bogus --skip Floats --setup MyTEXT --setup-doctest",
        "usage: CollectSection [-h] [--skip TEXT] [--fail-nocode] [--setup TEXT]",
        "                      [--teardown TEXT] [--setup-doctest]",
        "                      file_glob",
    ]
    expected_lines2 = [
        "Process a line of ini file phmdoctest-collect section.",
    ]
    expected_lines3 = [
        # "positional arguments:",
        "  file_glob             Generate test file for matching markdown file.",
    ]
    expected_lines4 = [
        # "optional arguments:",
        # "  -h, --help            show this help message and exit",
        "  --skip TEXT, -s TEXT",
        "  --fail-nocode",
        "  --setup TEXT, -u TEXT",
        "  --teardown TEXT, -d TEXT",
        "  --setup-doctest",
    ]
    # Replace all run of whitespace including newlines with spaces.
    got = re.sub(r"\s+", " ", parsed["ini-error"])
    # Check that text from the four groups of lines is present
    # somewhere in the "ini-error" value.
    want1 = re.sub(r"\s+", " ", "\n".join(expected_lines1))
    want2 = re.sub(r"\s+", " ", "\n".join(expected_lines2))
    want3 = re.sub(r"\s+", " ", "\n".join(expected_lines3))
    want4 = re.sub(r"\s+", " ", "\n".join(expected_lines4))
    assert want1 in got
    assert want2 in got
    assert want3 in got
    assert want4 in got


def show_args(line: str) -> None:
    """Show the dict created by parsing a collect section line.

    If the parsing fails, catch and print the exception message instead.
    """
    parser = make_collect_parser()
    try:
        args = parse_collect_line(parser, line)
        glob = args.pop("file_glob")
        print("glob=", glob)
        print("args=", args)
    except ValueError as exc_info:
        print("Caught ValueError from parse_collect_lines...")
        print(exc_info)


def _main():
    """Show some lines and the parsing results."""
    lines = [
        "doc/*.md --skip Floats --setup MyTEXT --setup-doctest",
        'doc/*.md --skip="Very small rocks" -sCIDER --setup=MyTEXT --setup-doctest --fail-nocode',
        'doc/*.md --skip="Very small rocks" --skip "CIDER" -uMyTEXT -d"tear me" --fail-nocode',
        "myglob --bogus",  # fails and prints help.
        "myglob --help",  # exits Python
    ]
    for line in lines:
        print()
        print(line)
        show_args(line)


if __name__ == "__main__":
    _main()
