# pytest-phmdoctest 1.0.0

## Introduction

Python syntax highlighted Markdown doctest pytest plugin.

A [pytest][4] plugin based on the [phmdoctest][3] command line tool.

If you have Python syntax highlighted examples in Markdown
like this:

Python code...
```python
print("Hello World!")
```
plus expected output.
```
Hello World!
```

and Python interactive sessions described by [doctest][1] ...

```python
>>> import math
>>> math.floor(9.1)
9
```
This [pytest][4] plugin will test them, as is, without edits.
On this file try the command ...
```shell
pytest -v --phmdoctest README.md
```
pytest console output ...
```
plugins: phmdoctest-0.0.3
collected 2 items

::README.py::README.session_00001_line_24 PASSED
::README.py::test_code_14_output_18 PASSED
```

* No blank line is needed after the doctest output: "9".
* On GitHub view top level README.md with the Raw mode to
  see the Python examples in fenced code blocks. Look for the
  triple back tick fence at the start of the line.

## Description

The plugin is based on the Python tool
[phmdoctest][3] version 1.3.
It generates a pytest test file from a Markdown file.

- Reads these from Markdown fenced code blocks:
  - Python interactive sessions described by [doctest][1].
  - Python source code and expected terminal output.
- Simple use case is possible with no Markdown edits.
- More features selected by adding HTML comment directives
  to the Markdown. See Directives in [phmdoctest][3].


### main branch status
[![](https://img.shields.io/pypi/l/pytest-phmdoctest.svg)](https://github.com/tmarktaylor/pytest-phmdoctest/blob/main/LICENSE.txt)
[![](https://img.shields.io/pypi/v/pytest-phmdoctest.svg)](https://pypi.python.org/pypi/pytest-phmdoctest)
[![](https://img.shields.io/pypi/pyversions/pytest-phmdoctest.svg)](https://pypi.python.org/pypi/pytest-phmdoctest)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[![CI Test](https://github.com/tmarktaylor/pytest-phmdoctest/actions/workflows/ci.yml/badge.svg)](https://github.com/tmarktaylor/pytest-phmdoctest/actions/workflows/ci.yml)
[![Build status](https://ci.appveyor.com/api/projects/status/fa0frmueq4h94v23/branch/main?svg=true)](https://ci.appveyor.com/project/tmarktaylor/pytest-phmdoctest/branch/main)
[![readthedocs](https://readthedocs.org/projects/pytest-phmdoctest/badge/?version=latest)](https://pytest-phmdoctest.readthedocs.io/en/latest/?badge=latest)
[![codecov](https://codecov.io/gh/tmarktaylor/pytest-phmdoctest/branch/main/graph/badge.svg?token=j5uu3WJn6u)](https://codecov.io/gh/tmarktaylor/pytest-phmdoctest/branch/main)

[Website](https://tmarktaylor.github.io/pytest-phmdoctest) |
[Docs](https://pytest-phmdoctest.readthedocs.io/en/latest/) |
[Repos](https://github.com/tmarktaylor/pytest-phmdoctest) |
[pytest](https://ci.appveyor.com/project/tmarktaylor/pytest-phmdoctest/branch/main) |
[Codecov](https://codecov.io/gh/tmarktaylor/pytest-phmdoctest/branch/main) |
[License](https://github.com/tmarktaylor/pytest-phmdoctest/blob/main/LICENSE.txt)


[Introduction](#introduction) |
[Description](#description) |
[Installation](#installation) |
[Usage](#usage) |
[Help](#help) |
[phmdoctest-collect](#phmdoctest-collect) |
[Saving test files](#saving-test-files) |
[Hints](#hints) |
[Related projects](#related-projects)


[Changes](doc/recent_changes.md) |
[Contributions](CONTRIBUTING.md)


## Installation
It is advisable to install in a virtual environment.

    python -m pip install pytest-phmdoctest

## Usage

Consider a project with the following files:

```text
CONTRIBUTING.md
README.md
doc/README.md
doc/directive2.md
doc/nocode.md
doc/project.md
tests/test_example.py
```

<!--phmdoctest-label plugin-inactive-command-->
```shell
pytest -v
```


<!--phmdoctest-label plugin-inactive-output-->
```text
plugins: phmdoctest-0.0.3
collected 1 item

tests/test_example.py::test_example PASSED
```

Use --phmdoctest to collect Markdown files.

<!--phmdoctest-label plugin-enabled-command-->
```shell
pytest --phmdoctest -v
```

<!--phmdoctest-label plugin-enabled-output-->
```text
plugins: phmdoctest-0.0.3
collected 11 items

::README.py::README.session_00001_line_24 PASSED
::README.py::test_code_10_output_17 PASSED
::doc__directive2.py::test_code_25_output_32 PASSED
::doc__directive2.py::test_code_42_output_47 PASSED
::doc__directive2.py::test_code_52_output_56 PASSED
::doc__nocode.py::test_nothing_passes PASSED
::doc__project.py::doc__project.session_00001_line_31 PASSED
::doc__project.py::doc__project.session_00002_line_46 PASSED
::doc__project.py::doc__project.session_00003_line_55 PASSED
::doc__project.py::test_code_12_output_19 PASSED
tests/test_example.py::test_example PASSED
```
- The sample project above can be viewed on GitHub at `tests/sample`.
- The doc__ indicates the Markdown file was collected from the
  doc folder.
- The plugin does not need the pytest option --doctest-modules.
- You can add --phmdoctest to the addopts section
  of a pytest configuration ini file. Pick one.
```ini
# pytest.ini and tox.ini
[pytest]
addopts = --phmdoctest
```
```ini
# setup.cfg
[tool:pytest]
addopts = --phmdoctest
```
```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--phmdoctest"
```

Markdown ".md" files are discovered by pytest.
pytest finds them in the same way it finds Python test files.
For each Markdown file discovered, the plugin generates a pytest
test file. The file is saved and collected from a
temporary directory managed by the plugin.
Some well known Markdown files get ignored automatically.
- README.md except at the repository root.
- All uppercase names like CONTRIBUTING.md.

If the Markdown file does not have any fenced code block examples
a test file with the test case named test_nothing_passes() is
generated and collected.

To avoid collecting .md files use pytest --ignore and --ignore-glob
on the command line or in the addopts part of the pytest ini file.
These commands work on .md files and use Unix shell-style wildcards.
```
# With a terminal in the tests/sample directory
# The first line collects 6 items.
# The second line collects 3 items.

pytest -v --phmdoctest --ignore README.md --ignore doc/directive2.md
pytest -v --phmdoctest --ignore-glob */*.md
```

## Help

pytest --help contains a **phmdoctest:** group in the middle and
an ini-option near the bottom.  The help contains:
- --phmdoctest
- --phmdoctest-save
- phmdoctest-collect

## phmdoctest-collect

An optional `phmdoctest-collect = ` section can be placed in the pytest
ini file. It is a list of lines of the format

    glob [phmdoctest command line options]

- The Markdown file must match one of the globs.
- The glob is processed by Path.glob() from the Python standard library pathlib.
  Path.glob() offers a "**" recursive pattern that means
  “this directory and all subdirectories, recursively”.
- The globs are checked from top to bottom. The first glob to match the Markdown
  file determines the phmdoctest command line options.
- If there is no match the file will **not** be collected.
- No files are auto ignored.
- A line can have just the glob and no options. The glob is required.
- The options should look like and have the same spacing as the command line
  options passed to the tool [phmdoctest][3].
  - Use double quotes as needed in TEXT.
  - The plugin does not support `\"` escaped double quote.
  - Look for list of options in the next section.
- If a line that does not parse is needed, the plugin collects
  a special test file that contains a failing test case with
  an embedded error message.

Example
```ini
# pytest.ini
[pytest]
addopts = --phmdoctest
phmdoctest-collect =
    doc/project.md
    **/*code.md --fail-nocode
```
Then run this pytest command on the project files from
the Usage section ...

<!--phmdoctest-label collect-section-command-->
```shell
pytest -v --ignore tests/test_example.py
```
output
<!--phmdoctest-label collect-section-output-->
```text
plugins: phmdoctest-0.0.3
collected 5 items

::doc__nocode.py::test_nothing_fails FAILED
::doc__project.py::doc__project.session_00001_line_31 PASSED
::doc__project.py::doc__project.session_00002_line_46 PASSED
::doc__project.py::doc__project.session_00003_line_55 PASSED
::doc__project.py::test_code_12_output_19 PASSED
```
- The glob on the first line matches the file doc/project.md generating
  the last 4 items in the output.
- The glob on the second line matches doc/nocode.md. The file
  does not have any examples. The phmdoctest option --fail-nocode
  tells phmdoctest to generate the test test_nothing_fails.
  That test results in the FAILED status of the first item
  collected.
- The ini file globs above only apply to .md files.
  We ignore the Python pytest test file tests/test_example.py
  by adding the --ignore option.

### phmdoctest-collect options

#### *-s, --skip TEXT*
Do not test blocks with substring TEXT. Allowed multiple times.

#### *--fail-nocode*
Markdown file with no code blocks generates a failing test.

#### *-u, --setup TEXT*
Run block with substring TEXT at test module setup time.

#### *-d, --teardown TEXT*
Run block with substring TEXT at test module teardown time.

#### *--setup-doctest*
Make globals created by the --setup Python code block
or setup directive visible to Python interactive session >>> blocks.
**Caution:** The globals are set at pytest Session scope.
The globals are visible to all doctests in the test suite.
This includes doctests collected by the plugin
and doctests collected from other files due to --doctest-modules.


## Saving test files

The generated pytest files can be saved for later
inspection using the `--phmdoctest-save` pytest command line
option. Specify a target directory for the files.
- The saved files have the prefix `test_`.
- If the directory exists it will be used, but not cleaned.
- If the directory does not exist, it is created.
- The plugin does not create a temporary directory.
- The plugin does not collect any files.
- pytest has been observed to collect test_*.py files saved
  to a pre-existing directory in the same invocation.


## Hints

- The plugin supports phmdoctest HTML comment directives that are placed in the
  Markdown. Among them are directives to designate setup, teardown,
  and skipped blocks.
- When invoking pytest, cwd must be in the subpath of the files to be collected
  to avoid this error from pathlib.py in relative_to():
  ValueError: `<file to be collected>` is not in the subpath of `<working directory>`
- Note the plugin does not accept single quoted phmdoctest args in the
  phmdoctest-collect section. A failing test will be collected.
- Use underscore in conftest.py for pytest_plugins:
  `pytest_plugins = ["pytest_phmdoctest"]`
- An ImportPathMismatchError indicates two test files have the same name.
- pytest -vv output shows the path to the plugin temporary directory.
- The --report option of the phmdoctest command lists all
  fenced code blocks in the Markdown file.

## Related projects

- phmdoctest
- rundoc
- byexample
- sphinx.ext.doctest
- sybil
- doxec
- egtest
- pytest-codeblocks

[1]: https://docs.python.org/3/library/doctest.html
[3]: https://tmarktaylor.github.io/phmdoctest
[4]: https://docs.pytest.org/en/stable
