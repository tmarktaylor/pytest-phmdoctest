"""Collect Python interactive sessions and possibly Python code/output."""
from pathlib import Path
import re
import textwrap
from typing import Optional

import pytest

import phmdoctest.tool
from . import collectors


def failing_test_case(built_from: str) -> str:
    """Return string containing a test. Test fails, prints message to stdout."""
    source = '''\


    def test_unable_to_collect_doctests():
        """Explain pytest-phmdoctest fails to process doctests."""
        error_message = """
    While building a collector for Python interactive sessions
    in the test file built from {} an error
    occured.  A DoctestModule.from_parent() call from
    pytest_phmdoctest.collectors.make_doctest_module() raised
    an exception.
    This may be due to using a version of pytest that
    has incompatible changes to this class.
    Here are some work-around ideas:
    - Try using --phmdoctest-generate option.
    - Make sure pytest >= 5.4.3.
    - Try using an older version of pytest like 6.2.x or 7.x.
    - Try using the separate PYPI package phmdoctest.
    - Add phmdoctest skip directives to the Markdown file on
      the Python interactive session fenced code blocks.
    - Add a glob and command line arguments to the phmdoctest-collect
      section in the ini file to skip the Python interactive session
      fenced code blocks.
    """
        print(error_message)
        assert False, "pytest-phmdoctest can't do doctests."
    '''
    source1 = source.format(built_from)
    return textwrap.dedent(source1)


def collect(
    markdown_examples: phmdoctest.tool.PythonExamples,
    built_from: str,
    parent: pytest.Collector,
    outfile_path: Path,
    collector_name: str,
) -> Optional[collectors.PluginCollector]:
    """Return a collector for one or both code/expected output and Python doctests.

    1. We collect Python code with expected output by collecting
       the generated test file with Module.
       We only need to collect a Module if Markdown has code examples.
    2. We collect Python interactive sessions by collecting the
       generated test file with DoctestModule.
    3. We don't collect Python interactive sessions if --phmdoctest.

    There may not be any of Python code with expected output or
    Python interactive sessions in the generated test file.
    See the docstring of phmdoctest.tool.detect_python_examples() for
     an explanation.

    If we have both Module and DoctestModule collectors we
    return a single Collector for both.

    This code is using the DoctestModule class.
    It is not part of the pytest API.
    """
    do_sessions = (
        parent.config.option.phmdoctest_docmod
        or parent.config.option.phmdoctest_generate
    ) and markdown_examples.has_session

    if markdown_examples.has_code and not do_sessions:
        return collectors.module(parent, outfile_path)

    docmod = collectors.doctest_module(parent, outfile_path)
    if docmod is None:
        # We can't build a DoctestModule to test the Python interactive
        # sessions (doctests) which might be in the test file.
        # It is possible Python interactive sessions in the Markdown
        # have been skipped by phmdoctest directives or the --skip
        # command line option.
        # Note that phmdoctest.tool.detect_python_examples()
        # used earlier does not consider phmdoctest directives or skips.
        # So we look in the generated test file for any ">>>"
        # substrings within raw triple quoted strings and assume they are
        # intended as a docstring for a doctest.
        # If we don't find any then we silently ignore that we can't build a
        # DoctestModule.
        #
        # Note: This hueristic could break if a future version of phmdoctest
        # generates doctests differently.
        # It is also possible that a user puts a raw triple quoted string
        # containing ">>>" in a Python code block. It would look like a
        # doctest here.
        #
        # If we have a doctest to collect, append a failing test case
        # with error message to the test file.
        # Note the test case is a pytest test function and so
        # we return a Module that collects it and any other pytest
        # functions in the generated test file.
        test_file = outfile_path.read_text(encoding="utf-8")
        pattern = r'r""".*?"""'  # raw triple quoted string
        raw_triple_quoted = re.findall(
            pattern=pattern, string=test_file, flags=re.DOTALL
        )
        if any(">>>" in docstring for docstring in raw_triple_quoted):
            extended_test_file = test_file + failing_test_case(built_from)
            _ = outfile_path.write_text(extended_test_file, encoding="utf-8")
            return collectors.module(parent, outfile_path)
        # We get here if docmod is None (failed) and skipped all markdown
        # doctests in the generated test file.

    if docmod and markdown_examples.has_code:
        mod = collectors.module(parent, outfile_path)
        bc = collectors.bundled_collector(parent, outfile_path, collector_name)
        bc.add_collectibles(docmod, mod)
        return bc
    elif docmod:
        return docmod
    elif markdown_examples.has_code:
        return collectors.module(parent, outfile_path)
    else:
        # Nothing to do.
        # We get here if:
        # 1. Failed to make docmod, but did not return the failing
        #    test case since there were no doctests in docstrings
        #    in the generated test file.
        # AND
        # 2. There were no code/expected output examples.
        return None
