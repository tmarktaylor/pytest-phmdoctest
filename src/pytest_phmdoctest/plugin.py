"""pytest-phmdoctest plugin implementation."""
from argparse import ArgumentParser
from pathlib import Path
import re
import textwrap

from tempfile import TemporaryDirectory
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import py

from _pytest import nodes
from _pytest.doctest import DoctestModule
from _pytest.nodes import Collector
from _pytest.python import Module
from _pytest.python import pytest_pycollect_makemodule

import phmdoctest.main


def pytest_addoption(parser):
    """pytest initialization hook."""
    group = parser.getgroup("phmdoctest")
    group.addoption(
        "--phmdoctest",
        action="store_true",
        help="Run Python code and Python interactive session examples in *.md files.",
    )
    group.addoption(
        "--phmdoctest-save",
        action="store",
        dest="phmdoctest_save",
        default=None,
        type=Path,
        metavar="dir",
        help="Generate pytest files from *.md files and store in dir for"
        " subsequent collection."
        " Each filename begins with 'test_'. '*__' denotes a folder named '*'"
        " that indicates the location of the Markdown file in the source tree."
        " If the directory does not exist, it is created. An existing directory is"
        " used as is, no files are removed. dir may be relative to pytest"
        " invocation dir or absolute.",
    )
    parser.addini(
        "phmdoctest-collect",
        type="linelist",
        help=(
            "each line is: glob [phmdoctest command line options]."
            " When this section exists, only glob matches are collected."
        ),
    )


def pytest_configure(config):
    """pytest initialization hook. Adds attributes to caller's config."""
    if config.option.phmdoctest:
        config._phmdoctest_temporary_dir = None
        config._phmdoctest_collect_section = CollectSection(config)


MyCollectibles = Tuple[DoctestModule, Module]


class MyCollector(Collector):
    """Collector for DoctestModule and Module."""

    _collectibles = (
        []
    )  # type: MyCollectibles  # Avoid nag "Instance attribute not def in __init__".

    def collect(self) -> MyCollectibles:
        """Override parent."""
        return self._collectibles

    def add_collectibles(self, docmod: DoctestModule, mod: Module) -> None:
        """Set the sequence of DoctestModule, Module to be collected."""
        self._collectibles = (docmod, mod)


def auto_ignore(root_path: Path, path: Path) -> bool:
    """Return True if a .md file should be ignored for collection.

    Allow README at pytest's root, but not elsewhere.
    Ignore all uppercase name anywhere.
    """
    if path.parent == root_path and path.stem == "README":
        return False
    else:
        return path.stem.upper() == path.stem


def pytest_collect_file(
    path: py.path.local, parent: nodes.Collector
) -> Optional[Union["Module", "MyCollector"]]:
    """pytest collection hook."""
    config = parent.config  # rename
    if config.option.phmdoctest and path.ext == ".md":
        collect_path = Path(path)
        invoke_path = Path(config.invocation_params.dir)
        relative_path = collect_path.relative_to(invoke_path)

        # If the ini file has a phmdoctest-collect section then
        # generate a test file if and only if the Markdown file matches a
        # glob in the section.
        # User may add phmdoctest command line args to the section.
        if config._phmdoctest_collect_section.exists():
            kwargs = config._phmdoctest_collect_section.match_glob(collect_path)
            if kwargs is None:
                return None

        # Since no phmdoctest-collect section in the .ini file check if file is
        # automatically ignored.
        elif auto_ignore(config.rootpath, collect_path):
            return None
        else:
            kwargs = {}  # use defaults.
        kwargs["markdown_file"] = collect_path
        # Express the built from filename in the generated testfile
        # docstring as a posix path. It will look the same when the plugin
        # is run on systems with Windows and non-Windows filesystems.
        kwargs["built_from"] = relative_path.as_posix()

        # Set the destination for the generated Python file.
        generated_stem = "__".join(relative_path.parts)  # flatten
        generated_name = Path(generated_stem).with_suffix(".py")
        if config.option.phmdoctest_save is None:
            if config._phmdoctest_temporary_dir is None:
                config._phmdoctest_temporary_dir = TemporaryDirectory()
            outfile_path = Path(config._phmdoctest_temporary_dir.name) / generated_name
        else:
            p: Path = config.option.phmdoctest_save
            if p.is_absolute():
                savers_dir = p
            else:
                savers_dir = config.invocation_params.dir / p
            savers_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            prefixed = "test_" + generated_name.stem
            prefixed_path = generated_name.with_name(prefixed + generated_name.suffix)
            outfile_path = savers_dir / prefixed_path

        if kwargs.get("ini-error", False):
            test_file = ini_error_file(kwargs["built_from"], kwargs["ini-error"])
        else:
            test_file = phmdoctest.main.testfile(**kwargs)
        with open(outfile_path, "w", encoding="utf-8") as fp:
            fp.write(test_file)

        if config.option.phmdoctest_save:
            return None  # Don't collect here.
        else:
            # Collect the generated pytest file from the temporary directory.
            # Collect a second time for the doctests in the docstrings.
            path = py.path.local(str(outfile_path))
            module: Module = pytest_pycollect_makemodule(path=path, parent=parent)
            docmod: DoctestModule = DoctestModule.from_parent(parent, fspath=path)
            mc = MyCollector.from_parent(
                parent, fspath=path, name=generated_stem
            )  # type: MyCollector
            mc.add_collectibles(docmod, module)
            return mc
    return None


def pytest_unconfigure(config):
    """pytest hook called before test process exits.  Cleanup the temporary dir."""
    if config.option.phmdoctest:
        if config._phmdoctest_temporary_dir is not None:
            config._phmdoctest_temporary_dir.cleanup()
            config._phmdoctest_temporary_dir = None


ArgValue = Union[List[str], str, bool]
"""Value of a keyword argument."""

ArgDict = Dict[str, ArgValue]
"""Arguments parsed from a line in phmdoctest-collect section."""


def ini_error_file(built_from, message):
    """Return string containing test file. Test fails, prints message to stdout."""
    source = '''\
    """pytest file built from {}"""


    def test_ini_failed():
        """Show a pytest-phmdoctest pytest ini file error."""
        error_message = """
    When checking if {} should be collected, an ini
    file parse error was discovered.
    {}"""
        print(error_message)
        assert False, "error in pytest-phmdoctest pytest ini file"
    '''
    source1 = textwrap.dedent(source)
    source2 = source1.format(built_from, built_from, message)
    return source2


class NoExitArgParser(ArgumentParser):
    """Instead of calling exit() raise a ValueError."""

    def error(self, message=None) -> None:  # type: ignore
        """Override ArgumentParser error handler."""
        raise ValueError()


def make_collect_parser():
    """Create ArgumentParser for one phmdoctest-collect ini line.

    Caution: Differs from Click parsing:
    1. Does not handle escaped double quotes in TEXT.
    """

    parser = NoExitArgParser(
        prog="CollectSection",  # must be the same as the class CollectSection
        description="Process a line of ini file phmdoctest-collect section.",
    )
    # The file glob is required.
    parser.add_argument(
        "file_glob",
        help="Generate test file for matching markdown file.",
    )
    # The following options are passed through to phmdoctest.
    parser.add_argument(
        "--skip",
        "-s",
        default=[],
        action="append",
        dest="skips",
        metavar="TEXT",
    )
    parser.add_argument("--fail-nocode", default=None, action="store_true")
    parser.add_argument("--setup", "-u", default=None, action="store", metavar="TEXT")
    parser.add_argument(
        "--teardown", "-d", default=None, action="store", metavar="TEXT"
    )
    parser.add_argument("--setup-doctest", default=None, action="store_true")
    return parser


def parse_collect_line(parser: NoExitArgParser, line: str) -> ArgDict:
    """Get the glob and make kwargs for Python call to phmdoctest.

    parser is an ArgumentParser for phmdoctest command line options.
    line is a line from the phmdoctest-collect section of pytest.ini.
        glob [phmdoctest command line options]

    Returns:
        Dict created by parsing the ini file line.
    """
    # Developers:
    # If a new option that takes TEXT is added, add code here
    # to replace its '='.
    #
    # Special code to handle a --skip TEXT where TEXT is double quoted.
    # For example
    #    --skip="Python 3.7"
    #         or
    #    --skip "Python 3.7"
    line1 = line.replace("--skip=", "--skip ")
    line2 = line1.replace("--setup=", "--setup ")
    line3 = line2.replace("--teardown=", "--teardown ")

    # 1. get characters between double quotes including the quotes
    # 2. get -s followed by 1.
    # 3. get -u followed by 1.
    # 4. get -d followed by 1.
    # 5. get runs of non-whitespace characters
    # Note: Can't use a double quote in TEXT.
    # Example: -s"TEXT" --> {skips: ['TEXT']}
    pattern = r'("[^"]*"|-[sud]"[^"]*"|\S+)'
    args1 = re.findall(pattern=pattern, string=line3)

    # Remove leading and trailing double quotes.
    args2a = [re.sub('^"([^"]*)"$', r"\1", arg) for arg in args1]

    # Remove start and end double quotes for -s, -u, -d
    # 1. if initial -s followed double quote.
    # 2. if initial -u followed double quote.
    # 3. if initial -d followed double quote.
    args2b = [re.sub('^(-[sud])"([^"]*)"$', r"\1\2", arg) for arg in args2a]

    try:
        args_namespace = parser.parse_args(args2b)
    except ValueError:
        text = "\n".join(
            [
                "pytest-phmdoctest parse error on the following line:",
                line,
                parser.format_help(),
            ]
        )
        return {"ini-error": text}
    return vars(args_namespace)


class CollectSection:
    """Check if path matches a glob in the phmdoctest-collect in pytest.ini.

    If a phmdoctest-collect section is present in a pytest configuration file
    check if the pytest_collect_file() path matches one of the globs
    in the section.  The globs are checked in file order.  If a glob
    matched the path, the rest of the line specifies the options for the
    call to phmdoctest.

    When this section exists a glob match is required for
    the file to be collected.

    Each line in the section starts with a file glob and is followed by
    zero or more phmdoctest command line options separated by spaces like this:

    glob [phmdoctest command line options]

    # pytest.ini
    phmdoctest-collect =
        README.md --fail-nocode
        doc/project.md --skip FIRST
        **/*.md

    The options are briefly described below.
    See phmdoctest --help and documentation for more detail.

    The parsing here is an approximation to what Click does.
    TEXT below can contain spaces if enclosed with double quotes.
    TEXT cannot contain any escaped double quotes.

    --skip, -s
        Do not test blocks with substring TEXT.
    --fail-nocode
        Markdown file with no code blocks generates a failing test.
    --setup, -u
        Run block with substring TEXT at test module setup time.
    --teardown, -d
        Run block with substring TEXT at test module teardown time.
    --setup-doctest
        Make globals created by the --setup Python code block
        or setup directive visible to Python interactive session >>> blocks.
        Caution: The globals are set at pytest Session scope and are visible
        to all tests in the test suite run by the plugin and regular
        python test files run by --doctest-modules.

    Use modified Python ArgumentParser to process the line.
    Create a keyword args dict to pass to phmdoctest.main.testfile().
    """

    def __init__(self, config) -> None:
        """Check for phmdoctest-collect ini section. If present, process it.

        Each line of the ini file section is parsed into a dict and
        stored in the list self._ini_lines. The key "ini-error" records
        an error message should parsing fail.
        """
        self._invoke_path = Path(config.invocation_params.dir)
        self._collect_ini = config.getini("phmdoctest-collect")
        self._ini_lines = []  # type: List[ArgDict]
        if self._collect_ini:
            parser = make_collect_parser()
            for line in self._collect_ini:
                self._ini_lines.append(parse_collect_line(parser, line))

    def exists(self) -> bool:
        """Return True if there is a phmdoctest-collect section in the .ini file.

        We expect it to be an empty list if the section is not present.
        """
        return len(self._collect_ini) > 0

    def match_glob(self, collect_path: Path) -> Optional[ArgDict]:
        """Check the parsed ini section for glob match. Return keyword args or None.

        Get the glob from the line and check if there is a match with
        collect_path. Return a keyword arguments dict containing
        phmdoctest command line arguments.

        The plugin detects a bad phmdoctest-collect line at pytest_configure()
        time. It remains silent until the line's file_glob is needed by
        pytest_collect_file(). The error text is saved in the
        ArgDict with key "ini-error".
        """
        for argdict in self._ini_lines:
            if argdict.get("ini-error", False):
                return argdict

            glob = argdict["file_glob"]
            if collect_path in self._invoke_path.glob(glob):
                kwargs = argdict.copy()
                kwargs.pop("file_glob")
                return kwargs
        return None
