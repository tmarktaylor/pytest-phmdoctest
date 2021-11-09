from pathlib import Path

import pytest


@pytest.fixture()
def testfile_checker(pytester, checker):
    """Return callable that compares pre existing file to testfile.

    This fixture is designed to run in a test case that injects the
    pytester fixture. pytester sets the current working directory
    to a temporary directory while it is active. pytester.copy_example()
    provides relative access to the project's directory.

    Caution: pytester.copy_example() writes a copy of file existing_filename
    at the pytester current working directory.
    """

    def check_it(existing_filename, testfile):
        """Compare pre existing file to testfile."""
        expected_file = pytester.copy_example(existing_filename)
        expected_contents = Path(expected_file).read_text(encoding="utf-8")
        checker(expected_contents, testfile)

    return check_it


def test_save_one(pytester, testfile_checker):
    """Generated testfile is saved and not collected, then collected and tested."""
    pytester.makeini("[pytest]\naddopts = --phmdoctest\n")
    pytester.copy_example("tests/sample/doc/directive2.md")
    pytester.mkdir("doc")
    Path("directive2.md").rename("doc/directive2.md")
    rr = pytester.runpytest("-v", "--phmdoctest-save", "savedir")
    assert rr.ret == pytest.ExitCode.NO_TESTS_COLLECTED
    rr.assert_outcomes(passed=0)
    assert Path("savedir").exists()
    assert Path("savedir/test_doc__directive2.py").exists()

    rr2 = pytester.runpytest("savedir", "-v")
    assert rr2.ret == pytest.ExitCode.OK
    rr2.assert_outcomes(passed=3)
    rr2.stdout.fnmatch_lines(
        [
            "*savedir/test_doc__directive2.py::test_code_25_output_32*",
            "*savedir/test_doc__directive2.py::test_code_42_output_47*",
            "*savedir/test_doc__directive2.py::test_code_52_output_56*",
        ],
        consecutive=True,
    )
    # Check the saved testfile contents.
    testfile = Path("savedir/test_doc__directive2.py").read_text(encoding="utf-8")
    testfile_checker("tests/expected/test_directive2.py", testfile)


def test_save_setup_doctest(pytester, testfile_checker):
    """Save a test file generated with the --setup-doctest option."""
    pytester.makefile(
        ".ini",
        pytest="""
        [pytest]
        addopts = --phmdoctest
        phmdoctest-collect =
            doc/setup_doctest.md -u FIRST -d LAST --setup-doctest
        """,
    )
    pytester.copy_example("tests/markdown/setup_doctest.md")
    pytester.mkdir("doc")
    Path("setup_doctest.md").rename("doc/setup_doctest.md")
    rr = pytester.runpytest("-v", "--phmdoctest-save", "savedir")
    assert rr.ret == pytest.ExitCode.NO_TESTS_COLLECTED
    rr.assert_outcomes(passed=0)
    assert Path("savedir").exists()
    assert Path("savedir/test_doc__setup_doctest.py").exists()

    rr2 = pytester.runpytest("savedir", "-v", "--doctest-modules")
    assert rr2.ret == pytest.ExitCode.OK
    rr2.assert_outcomes(passed=6)
    rr2.stdout.fnmatch_lines(
        [
            "*savedir/test_doc__setup_doctest.py::test_doc__setup_doctest.session_00000*",
            "*savedir/test_doc__setup_doctest.py::test_doc__setup_doctest.session_00001_line_69*",
            "*savedir/test_doc__setup_doctest.py::test_doc__setup_doctest.session_00002_line_76*",
            "*savedir/test_doc__setup_doctest.py::test_code_20_output_27*",
            "*savedir/test_doc__setup_doctest.py::test_code_37_output_42*",
            "*savedir/test_doc__setup_doctest.py::test_code_47_output_51*",
        ],
        consecutive=True,
    )
    # Check the saved testfile contents.
    testfile = Path("savedir/test_doc__setup_doctest.py").read_text(encoding="utf-8")
    testfile_checker("tests/expected/test_setup_doctest.py", testfile)


def test_save_to_existing_dir(pytester):
    """Generated testfile saved to pre-existing dir and gets collected from it.

    Note we populate doc/project.md.
    When running pytest on generated test files, the pytest --doctest-modules
    is needed to test the Python interactive sessions.

    This example takes advantage of the following observations:
    1. pytest does collection for the plugin before normal test collection.
    2. pytest won't collect from a dir created at the hook pytest_collect_file()
       time.
    3. pytest does collect from a dir that existed before runpytest() even
       though it was empty at the time.
    """
    pytester.mkdir("savedir")
    pytester.makeini("[pytest]\naddopts = --phmdoctest\n")
    pytester.copy_example("tests/sample/doc/project.md")
    pytester.mkdir("doc")
    Path("project.md").rename("doc/project.md")
    rr = pytester.runpytest("-v", "--phmdoctest-save", "savedir", "--doctest-modules")
    assert rr.ret == pytest.ExitCode.OK
    assert Path("savedir/test_doc__project.py").exists()
    rr.assert_outcomes(passed=4)
    rr.stdout.fnmatch_lines(
        [
            "*savedir/test_doc__project.py::test_doc__project.session_00001_line_31*",
            "*savedir/test_doc__project.py::test_doc__project.session_00002_line_46*",
            "*savedir/test_doc__project.py::test_doc__project.session_00003_line_55*",
            "*savedir/test_doc__project.py::test_code_12_output_19*",
        ],
        consecutive=True,
    )

    # Run again selecting root to be collected.  This will generate and collect
    # overwriting the populated savedir.  We expect the failing test to get
    # overwritten.
    # Modify savedir/test_doc__project.py so it fails.
    filename = "savedir/test_doc__project.py"
    contents = Path(filename).read_text(encoding="utf-8")
    failing_test = "\ndef test_fails():\n    assert False, 'intentionally failing test'"
    contents += failing_test
    with open(filename, "w", encoding="utf-8") as f:
        f.write(contents)

    # Show there is now a failing test in savedir.
    rr2 = pytester.runpytest("savedir", "-v", "--doctest-modules")
    assert rr2.ret == pytest.ExitCode.TESTS_FAILED
    rr2.assert_outcomes(failed=1, passed=4)
    assert Path("savedir/test_doc__project.py").exists()

    # Put test_directive2.py in savedir before running with --phmdoctest-save
    # to show pre-existing file in savedir is preserved.
    # This run collects savedir/test_directive2.py and generates and collects
    # savedir/test_doc__project.py.
    pytester.copy_example("tests/expected/test_directive2.py")
    Path("test_directive2.py").rename("savedir/test_directive2.py")
    assert Path("savedir/test_directive2.py").exists()
    rr3 = pytester.runpytest("-v", "--doctest-modules", "--phmdoctest-save", "savedir")
    assert rr3.ret == pytest.ExitCode.OK
    rr3.assert_outcomes(passed=7)
    rr3.stdout.fnmatch_lines(
        [
            "*savedir/test_directive2.py::test_code_25_output_32*",
            "*savedir/test_directive2.py::test_code_42_output_47*",
            "*savedir/test_directive2.py::test_code_52_output_56*",
            "*savedir/test_doc__project.py::test_doc__project.session_00001_line_31*",
            "*savedir/test_doc__project.py::test_doc__project.session_00002_line_46*",
            "*savedir/test_doc__project.py::test_doc__project.session_00003_line_55*",
            "*savedir/test_doc__project.py::test_code_12_output_19*",
        ],
        consecutive=True,
    )


def test_save_all(pytester, file_creator):
    """Generated testfiles are saved and not collected, then collected and tested.

    Note that tests/test_example.py is collected by pytest normally
    since it is not a .md file.
    When running pytest on generated test files, the pytest --doctest-modules
    is needed to test the Python interactive sessions.
    """
    pytester.makeini("[pytest]\naddopts = --phmdoctest\n")
    file_creator.populate_all(pytester_object=pytester)
    rr = pytester.runpytest("-v", "--phmdoctest-save", "savedir")
    assert rr.ret == pytest.ExitCode.OK
    rr.assert_outcomes(passed=1)
    rr.stdout.fnmatch_lines(
        [
            "*tests/test_example.py::test_example*",
        ]
    )

    assert Path("savedir").exists()
    assert Path("savedir/test_doc__directive2.py").exists()
    assert Path("savedir/test_doc__nocode.py").exists()
    assert Path("savedir/test_doc__project.py").exists()
    assert Path("savedir/test_README.py").exists()
    assert len(list(Path("savedir").iterdir())) == 4

    # auto-ignored files did not get collected.
    assert not Path("savedir/test_CONTRIBUTING.py").exists()

    rr2 = pytester.runpytest("tests", "savedir", "-v", "--doctest-modules")
    assert rr2.ret == pytest.ExitCode.OK
    rr2.assert_outcomes(passed=11)
    rr2.stdout.fnmatch_lines(
        [
            "*tests/test_example.py::test_example*",
            "*savedir/test_README.py::test_README.session_00001_line_24*",
            "*savedir/test_README.py::test_code_10_output_17*",
            "*savedir/test_doc__directive2.py::test_code_25_output_32*",
            "*savedir/test_doc__directive2.py::test_code_42_output_47*",
            "*savedir/test_doc__directive2.py::test_code_52_output_56*",
            "*savedir/test_doc__nocode.py::test_nothing_passes*",
            "*savedir/test_doc__project.py::test_doc__project.session_00001_line_31*",
            "*savedir/test_doc__project.py::test_doc__project.session_00002_line_46 PASSED*",
            "*savedir/test_doc__project.py::test_doc__project.session_00003_line_55 PASSED*",
            "*savedir/test_doc__project.py::test_code_12_output_19*",
        ],
        consecutive=True,
    )


def test_save_all_absolute(pytester, file_creator):
    """Same as test_save_all() but --phmdoctest-save is an absolute path.

    When running pytest on generated test files, the pytest --doctest-modules
    is needed to test the Python interactive sessions.
    Note that tests/test_example.py is collected by pytest normally
    since it is not a .md file.
    """
    pytester.makeini("[pytest]\naddopts = --phmdoctest\n")
    file_creator.populate_all(pytester_object=pytester)
    abssavedir = Path().cwd() / "mysavedir"
    assert abssavedir.is_absolute()
    rr = pytester.runpytest("-v", "--phmdoctest-save", str(abssavedir))
    assert rr.ret == pytest.ExitCode.OK
    rr.assert_outcomes(passed=1)
    rr.stdout.fnmatch_lines(
        [
            "*tests/test_example.py::test_example*",
        ]
    )

    assert Path("mysavedir").exists()
    assert len(list(Path("mysavedir").iterdir())) == 4
    assert Path("mysavedir/test_doc__directive2.py").exists()
    assert Path("mysavedir/test_doc__nocode.py").exists()
    assert Path("mysavedir/test_doc__project.py").exists()
    assert Path("mysavedir/test_README.py").exists()

    # auto-ignored files did not get collected.
    assert not Path("mysavedir/test_CONTRIBUTING.py").exists()

    rr2 = pytester.runpytest("tests", "mysavedir", "-v", "--doctest-modules")
    assert rr2.ret == pytest.ExitCode.OK
    rr2.assert_outcomes(passed=11)
    rr2.stdout.fnmatch_lines(
        [
            "*tests/test_example.py::test_example*",
            "*mysavedir/test_README.py::test_README.session_00001_line_24*",
            "*mysavedir/test_README.py::test_code_10_output_17*",
            "*mysavedir/test_doc__directive2.py::test_code_25_output_32*",
            "*mysavedir/test_doc__directive2.py::test_code_42_output_47*",
            "*mysavedir/test_doc__directive2.py::test_code_52_output_56*",
            "*mysavedir/test_doc__nocode.py::test_nothing_passes*",
            "*mysavedir/test_doc__project.py::test_doc__project.session_00001_line_31*",
            "*mysavedir/test_doc__project.py::test_doc__project.session_00002_line_46 PASSED*",
            "*mysavedir/test_doc__project.py::test_doc__project.session_00003_line_55 PASSED*",
            "*mysavedir/test_doc__project.py::test_code_12_output_19*",
        ],
        consecutive=True,
    )
