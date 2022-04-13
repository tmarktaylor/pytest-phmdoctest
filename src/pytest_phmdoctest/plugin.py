"""pytest-phmdoctest plugin implementation."""
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

import py
import pytest

import phmdoctest.main
import phmdoctest.tool
from . import docmod
from . import collectors
from . import settings


PHMDOCTEST = "--phmdoctest"
DOCMOD = "--phmdoctest-docmod"
GENERATE = "--phmdoctest-generate"


def as_dest(opt: str) -> str:
    """Reformat parser opt as an identifier for addoption() dest."""
    undashdashed = opt.replace("--", "")
    return undashdashed.replace("-", "_")


def pytest_addoption(parser):
    """pytest initialization hook."""
    group = parser.getgroup("phmdoctest")
    group.addoption(
        PHMDOCTEST,
        action="store_true",
        dest=as_dest(opt=PHMDOCTEST),
        help="Test Python code/expected output (no doctests) examples in *.md files.",
    )
    group.addoption(
        DOCMOD,
        action="store_true",
        dest=as_dest(opt=DOCMOD),
        help="Or run Python and doctest examples using pytest non-public API.",
    )
    group.addoption(
        GENERATE,
        action="store",
        dest=as_dest(opt=GENERATE),
        default=None,
        type=Path,
        metavar="DIR",
        help="Or write pytest files generated from Python and doctest examples to DIR.",
    )
    parser.addini(
        "phmdoctest-collect",
        type="linelist",
        help=(
            "each line is: glob [options]."
            " When this section exists, only glob matches are collected."
        ),
    )


def with_stem(path: Path, stem: str) -> Path:
    """Replacement for pathlib.PurePath.with_stem() which is new Python 3.9."""
    return path.with_name(stem + path.suffix)


def purge_markdown_from(target_dir: Path) -> None:
    """Clean target_dir directory of any Markdown files.

    Prevent future collection of pre-existing .md files in target_dir.
    The FILENAME.md files found in target_dir are renamed
    to FILENAME_md.sav.
    """

    for existing_path in target_dir.glob("*.md"):
        preserve_path = existing_path.with_suffix(".sav")
        preserve_path = with_stem(preserve_path, existing_path.stem + "_md")
        existing_path.replace(preserve_path)


def pytest_configure(config):
    """pytest initialization hook. Adds attributes to caller's config."""
    # Only one option allowed:
    if (
        (config.option.phmdoctest and config.option.phmdoctest_generate)
        or (config.option.phmdoctest and config.option.phmdoctest_docmod)
        or (config.option.phmdoctest_generate and config.option.phmdoctest_docmod)
    ):
        raise pytest.UsageError(
            "pytest-phmdoctest plugin usage error. "
            f"Cannot use more than one of {PHMDOCTEST}, {GENERATE}, "
            f"{DOCMOD} option at the same time."
        )
    # Ini-file collect section allowed in all modes.
    if (
        config.option.phmdoctest
        or config.option.phmdoctest_generate
        or config.option.phmdoctest_docmod
    ):
        config.phmdoctest_file_settings = settings.FileSettings(config)
    # Temporary directory needed in non-generate modes.
    if config.option.phmdoctest or config.option.phmdoctest_docmod:
        config.phmdoctest_temporary_dir = None

    # For generate mode:
    # Create directory DIR for writing generated pytest files.
    # 1. The FILENAME.py files found in DIR are renamed to noFILENAME.sav.
    # 2. If a noFILENAME.sav already exists it is not modified.
    # 3. Markdown (*.md) files are renamed to *_md.sav.
    # 4. Files in DIR with other extensions are not modified.
    #
    # This results in 2 important outcomes:
    # 1. The FILENAME.py files remaining in DIR after plugin collection are
    #    generated test_FILENAME.py files from the current pytest invocation.
    # 2. A FILENAME.py pre-existing in DIR is only renamed and not deleted.
    #    This allows for recovery of FILENAME.py files when DIR gets pointed
    #    by mistake to a directory with Python source files.
    if config.option.phmdoctest_generate is not None:
        p: Path = config.option.phmdoctest_generate
        if p.is_absolute():
            generate_dir = p
        else:
            generate_dir = config.invocation_params.dir / p
        config.phmdoctest_filesystem_dir = Path(generate_dir)
        phmdoctest.tool.wipe_testfile_directory(generate_dir)
        purge_markdown_from(generate_dir)


# Please be aware that mypy says error: All conditional function variants
# must have identical signatures.
if collectors.PYTEST_GE_7:

    def pytest_collect_file(
        file_path: Path, parent: pytest.Collector
    ) -> Optional[collectors.PluginCollector]:
        """pytest collection hook for pytest version 7.x."""
        pathy = collectors.Pathy(file_path)
        return pathy_collect_file(pathy, parent)


else:

    def pytest_collect_file(
        path: py.path.local, parent: pytest.Collector
    ) -> Optional[collectors.PluginCollector]:
        """pytest collection hook for pytest version 6.2.x."""
        pathy = collectors.Pathy(path)
        return pathy_collect_file(pathy, parent)


def pathy_collect_file(
    markdown: collectors.Pathy, parent: pytest.Collector
) -> Optional[collectors.PluginCollector]:
    """pytest collection hook implemntation."""
    config = parent.config  # rename
    if (
        config.option.phmdoctest
        or config.option.phmdoctest_generate
        or config.option.phmdoctest_docmod
    ) and markdown.extension == ".md":
        collect_path = markdown.as_path
        invoke_path = Path(config.invocation_params.dir)
        markdown_examples = phmdoctest.tool.detect_python_examples(collect_path)

        # Don't try collecting a .md file with no
        # Python highlighted fenced code blocks.
        if not (markdown_examples.has_code or markdown_examples.has_session):
            # The empty collector avoids a pytest error when individual
            # .md files are specified on the command line.
            # The error shows up as a Usage error in pytest's debug log.
            return collectors.empty_collector(parent, markdown, collect_path.name)

        # If the ini file has a phmdoctest-collect section then
        # generate a test file if and only if the Markdown file matches a
        # glob in the section.
        # User may add options to the section.
        if config.phmdoctest_file_settings.exists():
            kwargs = config.phmdoctest_file_settings.match_glob(collect_path)
            if kwargs is None:
                return collectors.empty_collector(parent, markdown, collect_path.name)
        else:
            kwargs = {}  # use defaults.
        kwargs["markdown_file"] = collect_path
        relative_path = collect_path.relative_to(invoke_path)
        kwargs["built_from"] = relative_path.as_posix()

        # 1. Name given to the collector which collects
        #    a Module and DoctestModule.
        #    It is a flattened version of the Markdown file.
        # 2. Its prefix names the generated test file.
        my_collector_name = "__".join(relative_path.parts)  # flatten

        # Set the destination for the generated Python test file.
        generated_path = Path(my_collector_name).with_suffix(".py")

        if config.option.phmdoctest_generate:
            prefixed = "test_" + generated_path.stem
            prefixed_path = with_stem(generated_path, prefixed)
            outfile_path = config.phmdoctest_filesystem_dir / prefixed_path
        else:
            # The other modes generate to the temp dir.
            if config.phmdoctest_temporary_dir is None:
                config.phmdoctest_temporary_dir = TemporaryDirectory()
            outfile_path = Path(config.phmdoctest_temporary_dir.name) / generated_path

        # Checking here for a line with a parse error in the phmdoctest-collect section.
        if "ini-error" in kwargs:
            test_file = settings.error_file(kwargs["built_from"], kwargs["ini-error"])
        else:
            test_file = phmdoctest.main.testfile(**kwargs)
        _ = outfile_path.write_text(test_file, encoding="utf-8")

        if config.option.phmdoctest_generate:
            # Don't collect here.
            # The intent is to collect the generated test files later in
            # the same pytest invocation by specifying the same dir
            # (as phmdoctest_filesystem_dir) further to the right
            # on the command line.
            #
            # If you don't want to collect the generated test files
            # specify a DIR where pytest won't try to cellect them.
            # See norecursedirs default values in Pytest Documentation |
            # API reference | Configuration Options | norecursedirs.
            return collectors.empty_collector(parent, markdown, collect_path.name)
        else:
            # Collect Module and/or DoctestModule
            plugin_collector = docmod.collect(
                markdown_examples=markdown_examples,
                built_from=kwargs["built_from"],
                parent=parent,
                outfile_path=outfile_path,
                collector_name=my_collector_name,
            )
            if plugin_collector:
                return plugin_collector
            else:
                return collectors.empty_collector(parent, markdown, collect_path.name)
    return None


def pytest_unconfigure(config):
    """pytest hook called before test process exits.  Cleanup the temporary dir."""
    # If we raised a UsageError in pytest_configure(), config.phmdoctest_temporary_dir
    # won't exist.
    if hasattr(config, "phmdoctest_temporary_dir"):
        if config.phmdoctest_temporary_dir is not None:
            config.phmdoctest_temporary_dir.cleanup()
            config.phmdoctest_temporary_dir = None
