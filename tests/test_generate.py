from pathlib import Path

import pytest


def test_generate_one(pytester, testfile_checker):
    """Generated testfile is saved and not collected, then collected and tested."""
    pytester.copy_example("tests/sample/doc/directive2.md")
    pytester.mkdir("doc")
    Path("directive2.md").rename("doc/directive2.md")
    rr = pytester.runpytest("-v", "--phmdoctest-generate", ".gendir")
    assert rr.ret == pytest.ExitCode.NO_TESTS_COLLECTED
    rr.assert_outcomes(passed=0)
    assert Path(".gendir").exists()
    assert Path(".gendir/test_doc__directive2.py").exists()

    rr2 = pytester.runpytest(".gendir", "-v")
    assert rr2.ret == pytest.ExitCode.OK
    rr2.assert_outcomes(passed=3)
    rr2.stdout.fnmatch_lines(
        [
            "*.gendir/test_doc__directive2.py::test_code_25_output_32*",
            "*.gendir/test_doc__directive2.py::test_code_42_output_47*",
            "*.gendir/test_doc__directive2.py::test_code_52_output_56*",
        ],
        consecutive=True,
    )
    # Check the saved testfile contents.
    testfile = Path(".gendir/test_doc__directive2.py").read_text(encoding="utf-8")
    testfile_checker("tests/expected/test_directive2.py", testfile)


def test_generate_setup_doctest(pytester, testfile_checker):
    """Save a test file generated with the --setup-doctest option."""
    pytester.makefile(
        ".ini",
        pytest="""
        [pytest]
        phmdoctest-collect =
            doc/setup_doctest.md -u FIRST -d LAST --setup-doctest
        """,
    )
    pytester.copy_example("tests/markdown/setup_doctest.md")
    pytester.mkdir("doc")
    Path("setup_doctest.md").rename("doc/setup_doctest.md")
    rr = pytester.runpytest("-v", "--phmdoctest-generate", ".gendir")
    assert rr.ret == pytest.ExitCode.NO_TESTS_COLLECTED
    rr.assert_outcomes(passed=0)
    assert Path(".gendir").exists()
    assert Path(".gendir/test_doc__setup_doctest.py").exists()

    rr2 = pytester.runpytest(".gendir", "-v", "--doctest-modules")
    assert rr2.ret == pytest.ExitCode.OK
    rr2.assert_outcomes(passed=6)
    rr2.stdout.fnmatch_lines(
        [
            "*.gendir/test_doc__setup_doctest.py::test_doc__setup_doctest.session_00000*",
            "*.gendir/test_doc__setup_doctest.py::test_doc__setup_doctest.session_00001_line_69*",
            "*.gendir/test_doc__setup_doctest.py::test_doc__setup_doctest.session_00002_line_76*",
            "*.gendir/test_doc__setup_doctest.py::test_code_20_output_27*",
            "*.gendir/test_doc__setup_doctest.py::test_code_37_output_42*",
            "*.gendir/test_doc__setup_doctest.py::test_code_47_output_51*",
        ],
        consecutive=True,
    )
    # Check the saved testfile contents.
    testfile = Path(".gendir/test_doc__setup_doctest.py").read_text(encoding="utf-8")
    testfile_checker("tests/expected/test_setup_doctest.py", testfile)


def test_generate_to_existing_dir(pytester):
    """Generated testfile saved to pre-existing dir and gets collected from it.

    Note we populate doc/project.md.
    When running pytest on saved test files, the pytest --doctest-modules
    is needed to test the Python interactive sessions.
    """
    pytester.mkdir(".gendir")
    pytester.copy_example("tests/sample/doc/project.md")
    pytester.mkdir("doc")
    Path("project.md").rename("doc/project.md")
    rr = pytester.runpytest(
        "-v", "--phmdoctest-generate", ".gendir", ".", ".gendir", "--doctest-modules"
    )
    assert rr.ret == pytest.ExitCode.OK
    assert Path(".gendir/test_doc__project.py").exists()
    rr.assert_outcomes(passed=4)
    rr.stdout.fnmatch_lines(
        [
            "*.gendir/test_doc__project.py::test_doc__project.session_00001_line_31*",
            "*.gendir/test_doc__project.py::test_doc__project.session_00002_line_46*",
            "*.gendir/test_doc__project.py::test_doc__project.session_00003_line_55*",
            "*.gendir/test_doc__project.py::test_code_12_output_19*",
        ],
        consecutive=True,
    )

    # Run again selecting root to be collected.  This will generate and collect
    # overwriting the populated savedir.  We expect the failing test to get
    # overwritten.
    # Modify savedir/test_doc__project.py so it fails.
    filename = ".gendir/test_doc__project.py"
    contents = Path(filename).read_text(encoding="utf-8")
    failing_test = "\ndef test_fails():\n    assert False, 'intentionally failing test'"
    contents += failing_test
    # with open(filename, "w", encoding="utf-8") as f:
    #     f.write(contents)
    _ = Path(filename).write_text(contents, encoding="utf-8")

    # Show there is now a failing test in .gendir.
    rr2 = pytester.runpytest(".gendir", "-v", "--doctest-modules")
    assert rr2.ret == pytest.ExitCode.TESTS_FAILED
    rr2.assert_outcomes(failed=1, passed=4)
    assert Path(".gendir/test_doc__project.py").exists()

    # Put test_directive2.py in .gendir before running with --phmdoctest-generate
    # to show pre-existing file in .gendir is preserved.
    # This run collects .gendir/test_directive2.py and generates and collects
    # .gendir/test_doc__project.py.
    pytester.copy_example("tests/expected/test_directive2.py")
    Path("test_directive2.py").rename(".gendir/test_directive2.py")
    assert Path(".gendir/test_directive2.py").exists()
    rr3 = pytester.runpytest(
        "-v", "--phmdoctest-generate", ".gendir", ".", ".gendir", "--doctest-modules"
    )
    assert rr3.ret == pytest.ExitCode.OK
    assert Path(".gendir/notest_directive2.sav").exists()
    rr3.assert_outcomes(passed=4)
    rr3.stdout.fnmatch_lines(
        [
            "*.gendir/test_doc__project.py::test_doc__project.session_00001_line_31*",
            "*.gendir/test_doc__project.py::test_doc__project.session_00002_line_46*",
            "*.gendir/test_doc__project.py::test_doc__project.session_00003_line_55*",
            "*.gendir/test_doc__project.py::test_code_12_output_19*",
        ],
        consecutive=True,
    )


def test_generate_all(pytester, file_creator):
    """Generated testfiles are saved and not collected, then collected and tested.

    Note that tests/test_example.py is collected by pytest normally
    since it is not a .md file.
    When running pytest on generated test files, the pytest --doctest-modules
    is needed to test the Python interactive sessions.
    """
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest(
        "-v",
        "--phmdoctest-generate",
        ".gendir",
        ".",
    )
    assert rr.ret == pytest.ExitCode.OK
    rr.assert_outcomes(passed=1)
    rr.stdout.fnmatch_lines(
        [
            "*tests/test_example.py::test_example*",
        ]
    )

    assert Path(".gendir").exists()
    assert Path(".gendir/test_doc__directive2.py").exists()
    assert Path(".gendir/test_doc__project.py").exists()
    assert Path(".gendir/test_README.py").exists()
    assert len(list(Path(".gendir").iterdir())) == 3

    # Files with no Python fenced code blocks did not get collected.
    assert not Path(".gendir/test_CONTRIBUTING.py").exists()

    rr2 = pytester.runpytest("tests", ".gendir", "-v", "--doctest-modules")
    assert rr2.ret == pytest.ExitCode.OK
    rr2.assert_outcomes(passed=10)
    rr2.stdout.fnmatch_lines(
        [
            "*tests/test_example.py::test_example*",
            "*.gendir/test_README.py::test_README.session_00001_line_24*",
            "*.gendir/test_README.py::test_code_10_output_17*",
            "*.gendir/test_doc__directive2.py::test_code_25_output_32*",
            "*.gendir/test_doc__directive2.py::test_code_42_output_47*",
            "*.gendir/test_doc__directive2.py::test_code_52_output_56*",
            "*.gendir/test_doc__project.py::test_doc__project.session_00001_line_31*",
            "*.gendir/test_doc__project.py::test_doc__project.session_00002_line_46 PASSED*",
            "*.gendir/test_doc__project.py::test_doc__project.session_00003_line_55 PASSED*",
            "*.gendir/test_doc__project.py::test_code_12_output_19*",
        ],
        consecutive=True,
    )


def test_generate_all_absolute(pytester, file_creator):
    """Same as test_generate_all() but --phmdoctest-generate is an absolute path.

    When running pytest on generated test files, the pytest --doctest-modules
    is needed to test the Python interactive sessions.
    Note that tests/test_example.py is collected by pytest normally
    since it is not a .md file.
    """
    file_creator.populate_all(pytester_object=pytester)
    abssavedir = Path().cwd() / ".mysavedir"
    assert abssavedir.is_absolute()
    rr = pytester.runpytest("-v", "--phmdoctest-generate", str(abssavedir), ".")
    assert rr.ret == pytest.ExitCode.OK
    rr.assert_outcomes(passed=1)
    rr.stdout.fnmatch_lines(
        [
            "*tests/test_example.py::test_example*",
        ]
    )

    assert Path(".mysavedir").exists()
    assert len(list(Path(".mysavedir").iterdir())) == 3
    assert Path(".mysavedir/test_doc__directive2.py").exists()
    assert Path(".mysavedir/test_doc__project.py").exists()
    assert Path(".mysavedir/test_README.py").exists()

    # Files with no Python fenced code blocks did not get collected.
    assert not Path(".mysavedir/test_CONTRIBUTING.py").exists()
    rr2 = pytester.runpytest("tests", ".mysavedir", "-v", "--doctest-modules")
    assert rr2.ret == pytest.ExitCode.OK
    rr2.assert_outcomes(passed=10)
    rr2.stdout.fnmatch_lines(
        [
            "*tests/test_example.py::test_example*",
            "*.mysavedir/test_README.py::test_README.session_00001_line_24*",
            "*.mysavedir/test_README.py::test_code_10_output_17*",
            "*.mysavedir/test_doc__directive2.py::test_code_25_output_32*",
            "*.mysavedir/test_doc__directive2.py::test_code_42_output_47*",
            "*.mysavedir/test_doc__directive2.py::test_code_52_output_56*",
            "*.mysavedir/test_doc__project.py::test_doc__project.session_00001_line_31*",
            "*.mysavedir/test_doc__project.py::test_doc__project.session_00002_line_46 PASSED*",
            "*.mysavedir/test_doc__project.py::test_doc__project.session_00003_line_55 PASSED*",
            "*.mysavedir/test_doc__project.py::test_code_12_output_19*",
        ],
        consecutive=True,
    )
