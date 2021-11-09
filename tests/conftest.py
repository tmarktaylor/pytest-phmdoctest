"""Fixtures used in by tests."""
import difflib
from pathlib import Path
from itertools import zip_longest

import pytest

pytest_plugins = ["pytester"]


@pytest.fixture()
def checker():
    """Return Callable(str, str) that runs difflib.ndiff. Multi-line str's ok."""

    def a_and_b_are_the_same(a, b):
        """Compare function with assert and line by line ndiff stdout."""
        a_lines = a.splitlines()
        b_lines = b.splitlines()
        for a_line, b_line in zip_longest(a_lines, b_lines):
            if a_line != b_line:
                diffs = difflib.ndiff(a_lines, b_lines)
                for line in diffs:
                    print(line)
                assert False

    return a_and_b_are_the_same


@pytest.fixture()
def file_creator():
    """Return an instance of FileCreator to copy example files to pytester."""

    class FileCreator:
        """Copy files to pytester temporary directory/"""

        def populate_root(self, pytester_object):
            """Copy .md files into pytester's working directory as shown below.

            CAUTION- When populating sub directories with filenames also present
            in the root:
                1. Create the files in the sub directories first.
                2. Call here last.
            pytester.copy_example() copies to the root overwriting any files
            already there of the same name.

            CONTRIBUTING.md
            README.md
            """
            pytester_object.copy_example("tests/sample/CONTRIBUTING.md")
            pytester_object.copy_example("tests/sample/README.md")

        def populate_doc(self, pytester_object):
            """Copy .md files into pytester's working directory as shown below.

            doc
                directive2.md
                nocode.md
                project.md
            """
            pytester_object.mkdir("doc")
            pytester_object.copy_example("tests/sample/doc/directive2.md")
            pytester_object.copy_example("tests/sample/doc/nocode.md")
            pytester_object.copy_example("tests/sample/doc/project.md")
            Path("directive2.md").rename("doc/directive2.md")
            Path("nocode.md").rename("doc/nocode.md")  # contains no test cases
            Path("project.md").rename("doc/project.md")

        def populate_all(self, pytester_object):
            """Copy .md and .py files into pytester's working directory as shown below.

            CONTRIBUTING.md
            README.md
            doc
                README.md
                directive2.md
                nocode.md
                project.md
            tests
                test_example.py
            """
            self.populate_doc(pytester_object=pytester_object)
            pytester_object.copy_example("tests/sample/doc/README.md")
            Path("README.md").rename("doc/README.md")
            self.populate_root(
                pytester_object=pytester_object
            )  # must be last of populates

            pytester_object.mkdir("tests")
            pytester_object.copy_example("tests/sample/tests/test_example.py")
            Path("test_example.py").rename("tests/test_example.py")
            assert Path("CONTRIBUTING.md").exists()
            assert Path("README.md").exists()
            assert Path("doc/README.md").exists()
            assert Path("doc/directive2.md").exists()
            assert Path("doc/nocode.md").exists()
            assert Path("doc/project.md").exists()
            assert Path("tests/test_example.py").exists()

    return FileCreator()
