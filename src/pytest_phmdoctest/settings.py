"""Parse and implement pytest registered ini-file options."""
from argparse import ArgumentParser
from pathlib import Path
import re
import textwrap
from typing import Dict
from typing import List
from typing import Optional
from typing import Union


def error_file(built_from: str, message: str) -> str:
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
    """Instead of calling sys.exit() raise a ValueError."""

    def error(self, message=None) -> None:  # type: ignore
        """Override ArgumentParser error handler."""
        raise ValueError()


ArgValue = Union[List[str], str, bool]
"""Value of a keyword argument."""

ArgDict = Dict[str, ArgValue]
"""Arguments parsed from a line in phmdoctest-collect section."""


def make_collect_parser() -> NoExitArgParser:
    """Create ArgumentParser for one phmdoctest-collect ini line.

    The options here mirror phmdoctest command line options.
    The intention is for the phmdoctest-collect section line
    to look the sane as a phmdoctest command line with the same options.

    Caution: Differs from Click parsing used by phmdoctest:
    1. Does not handle escaped double quotes in TEXT.
    """

    parser = NoExitArgParser(
        prog="FileSettings",  # must be the same as the class FileSettings
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
        glob [options]

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


class FileSettings:
    """Check if path is selected by a configuration setting.

    Configuration settings may be found in collect section in pytest's ini file.
    A phmdoctest-collect section may be present in a pytest configuration file.
    The logic checks if the pytest_collect_file() path matches one of the globs
    in the section.  The globs are checked in file order.  If a glob
    matched the path, the rest of the line specifies the options for the
    call to phmdoctest.

    When this section exists a glob match is required for
    a file with Python syntax highlighted fenced code blocks to be collected.

    Each line in the section starts with a file glob and is followed by
    zero or more phmdoctest command line options separated by spaces like this:

    glob [options]

    # pytest.ini
    phmdoctest-collect =
        doc/project.md --skip greeting --skip enjoyment
        **/*.md

    The options are briefly described below.
    See phmdoctest --help and documentation for more detail.

    The parsing here is an approximation to what Click does.
    TEXT below can contain spaces if enclosed with double quotes.
    TEXT cannot contain any escaped double quotes.

    --skip, -s
        Do not test blocks with substring TEXT.
    --fail-nocode
        Markdown file with no code blocks left after applying skips
        generates a failing test.
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
        """Process configuration from pytest ini file.

        An ini file has a phmdoctest-collect section.
        Each line of the ini file section is parsed into a dict and
        stored in the list self.args. The key "ini-error" records
        an error message should parsing fail.
        """
        self.invoke_path = Path(config.invocation_params.dir)
        self.section = config.getini("phmdoctest-collect")
        self.args = []  # type: List[ArgDict]
        if self.section:
            # Process the ini file phmdoctest-collect section.
            parser = make_collect_parser()
            for line in self.section:
                self.args.append(parse_collect_line(parser, line))

    def exists(self) -> bool:
        """True if we found settings in a config file or ini file section."""
        return len(self.args) > 0

    def match_glob(self, collect_path: Path) -> Optional[ArgDict]:
        """Check the parsed settings for glob match. Return keyword args or None.

        Check each args item's file_glob value for a match with collect_path.
        Return dict containing phmdoctest command line arguments.

        The plugin detects a bad phmdoctest-collect line at pytest_configure()
        time. It remains silent until the line's file_glob is needed by
        pytest_collect_file(). The error text is saved in the
        ArgDict with key "ini-error".
        """
        for argdict in self.args:
            if "ini-error" in argdict:
                return argdict

            glob: str = argdict["file_glob"]
            if collect_path in self.invoke_path.glob(glob):
                kwargs = argdict.copy()
                kwargs.pop("file_glob")
                return kwargs
        return None
