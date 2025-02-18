"""
Tests for `doccmd`.
"""

import stat
import subprocess
import sys
import textwrap
import uuid
from collections.abc import Sequence
from pathlib import Path

import pytest
from click.testing import CliRunner
from pytest_regressions.file_regression import FileRegressionFixture

from doccmd import main


def test_help(file_regression: FileRegressionFixture) -> None:
    """Expected help text is shown.

    This help text is defined in files.
    To update these files, run ``pytest`` with the ``--regen-all`` flag.
    """
    runner = CliRunner(mix_stderr=False)
    arguments = ["--help"]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    file_regression.check(contents=result.output)


def test_run_command(tmp_path: Path) -> None:
    """
    It is possible to run a command against a code block in a document.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    content = """\
    .. code-block:: python

        x = 2 + 2
        assert x == 4
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        # The file is padded so that any error messages relate to the correct
        # line number in the original file.
        text="""\


        x = 2 + 2
        assert x == 4
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_double_language(tmp_path: Path) -> None:
    """
    Giving the same language twice does not run the command twice.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    content = """\
    .. code-block:: python

        x = 2 + 2
        assert x == 4
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--language",
        "python",
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        # The file is padded so that any error messages relate to the correct
        # line number in the original file.
        text="""\


        x = 2 + 2
        assert x == 4
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_file_does_not_exist() -> None:
    """
    An error is shown when a file does not exist.
    """
    runner = CliRunner(mix_stderr=False)
    arguments = [
        "--language",
        "python",
        "--command",
        "cat",
        "non_existent_file.rst",
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code != 0
    assert "Path 'non_existent_file.rst' does not exist" in result.stderr


def test_not_utf_8_file_given(tmp_path: Path) -> None:
    """
    No error is given if a file is passed in which is not UTF-8.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    content = """\
    .. code-block:: python

       print("\xc0\x80")
    """
    rst_file.write_text(data=content, encoding="latin1")
    arguments = [
        "--language",
        "python",
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = ""
    assert result.stdout == expected_output
    assert result.stderr == ""


def test_multiple_code_blocks(tmp_path: Path) -> None:
    """
    It is possible to run a command against multiple code blocks in a document.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    content = """\
    .. code-block:: python

        x = 2 + 2
        assert x == 4

    .. code-block:: python

        y = 3 + 3
        assert y == 6
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        text="""\


        x = 2 + 2
        assert x == 4







        y = 3 + 3
        assert y == 6
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_language_filters(tmp_path: Path) -> None:
    """
    Languages not specified are not run.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    content = """\
    .. code-block:: python

        x = 2 + 2
        assert x == 4

    .. code-block:: javascript

        var y = 3 + 3;
        console.assert(y === 6);
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        text="""\


        x = 2 + 2
        assert x == 4
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_run_command_no_pad_file(tmp_path: Path) -> None:
    """
    It is possible to not pad the file.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    content = """\
    .. code-block:: python

        x = 2 + 2
        assert x == 4
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--command",
        "cat",
        "--no-pad-file",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        text="""\
        x = 2 + 2
        assert x == 4
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_multiple_files(tmp_path: Path) -> None:
    """
    It is possible to run a command against multiple files.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file1 = tmp_path / "example1.rst"
    rst_file2 = tmp_path / "example2.rst"
    content1 = """\
    .. code-block:: python

        x = 2 + 2
        assert x == 4
    """
    content2 = """\
    .. code-block:: python

        y = 3 + 3
        assert y == 6
    """
    rst_file1.write_text(data=content1, encoding="utf-8")
    rst_file2.write_text(data=content2, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--command",
        "cat",
        str(object=rst_file1),
        str(object=rst_file2),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        text="""\


        x = 2 + 2
        assert x == 4


        y = 3 + 3
        assert y == 6
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_multiple_files_multiple_types(tmp_path: Path) -> None:
    """
    It is possible to run a command against multiple files of multiple types
    (Markdown and rST).
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    md_file = tmp_path / "example.md"
    rst_content = """\
    .. code-block:: python

       print("In reStructuredText code-block")

    .. code:: python

       print("In reStructuredText code")
    """
    md_content = """\
    ```python
    print("In simple markdown code block")
    ```

    ```{code-block} python
    print("In MyST code-block")
    ```

    ```{code} python
    print("In MyST code")
    ```
    """
    rst_file.write_text(data=rst_content, encoding="utf-8")
    md_file.write_text(data=md_content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--command",
        "cat",
        "--no-pad-file",
        str(object=rst_file),
        str(object=md_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        text="""\
        print("In reStructuredText code-block")
        print("In reStructuredText code")
        print("In simple markdown code block")
        print("In MyST code-block")
        print("In MyST code")
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_modify_file(tmp_path: Path) -> None:
    """
    Commands can modify files.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    content = """\
    .. code-block:: python

        a = 1
        b = 1
        c = 1
    """
    rst_file.write_text(data=content, encoding="utf-8")
    modify_code_script = textwrap.dedent(
        text="""\
        #!/usr/bin/env python

        import sys

        with open(sys.argv[1], "w") as file:
            file.write("foobar")
        """,
    )
    modify_code_file = tmp_path / "modify_code.py"
    modify_code_file.write_text(data=modify_code_script, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--command",
        f"python {modify_code_file.as_posix()}",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    modified_content = rst_file.read_text(encoding="utf-8")
    expected_modified_content = """\
    .. code-block:: python

        foobar
    """
    assert modified_content == expected_modified_content


def test_exit_code(tmp_path: Path) -> None:
    """
    The exit code of the first failure is propagated.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    exit_code = 25
    content = f"""\
    .. code-block:: python

        import sys
        sys.exit({exit_code})
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--command",
        Path(sys.executable).as_posix(),
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == exit_code


@pytest.mark.parametrize(
    argnames=("language", "expected_extension"),
    argvalues=[
        ("python", ".py"),
        ("javascript", ".js"),
    ],
)
def test_file_extension(
    tmp_path: Path,
    language: str,
    expected_extension: str,
) -> None:
    """
    The file extension of the temporary file is appropriate for the language.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    content = f"""\
    .. code-block:: {language}

        x = 2 + 2
        assert x == 4
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--language",
        language,
        "--command",
        "echo",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    output = result.stdout
    output_path = Path(output.strip())
    assert output_path.suffix == expected_extension


def test_given_temporary_file_extension(tmp_path: Path) -> None:
    """
    It is possible to specify the file extension for created temporary files.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    content = """\
    .. code-block:: python

        x = 2 + 2
        assert x == 4
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--temporary-file-extension",
        ".foobar",
        "--command",
        "echo",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    output = result.stdout
    output_path = Path(output.strip())
    assert output_path.suffixes == [".foobar"]


def test_given_temporary_file_extension_no_leading_period(
    tmp_path: Path,
) -> None:
    """
    An error is shown when a given temporary file extension is given with no
    leading period.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    content = """\
    .. code-block:: python

        x = 2 + 2
        assert x == 4
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--temporary-file-extension",
        "foobar",
        "--command",
        "echo",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code != 0, (result.stdout, result.stderr)
    assert result.stdout == ""
    expected_stderr = textwrap.dedent(
        text="""\
        Usage: doccmd [OPTIONS] [DOCUMENT_PATHS]...
        Try 'doccmd --help' for help.

        Error: Invalid value for '--temporary-file-extension': 'foobar' does not start with a '.'.
        """,  # noqa: E501
    )
    assert result.stderr == expected_stderr


def test_given_prefix(tmp_path: Path) -> None:
    """
    It is possible to specify a prefix for the temporary file.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    content = """\
    .. code-block:: python

        x = 2 + 2
        assert x == 4
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--temporary-file-name-prefix",
        "myprefix",
        "--command",
        "echo",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    output = result.stdout
    output_path = Path(output.strip())
    assert output_path.name.startswith("myprefix_")


def test_file_extension_unknown_language(tmp_path: Path) -> None:
    """
    The file extension of the temporary file is `.txt` for any unknown
    language.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    content = """\
    .. code-block:: unknown

        x = 2 + 2
        assert x == 4
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--language",
        "unknown",
        "--command",
        "echo",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    output = result.stdout
    output_path = Path(output.strip())
    assert output_path.suffix == ".txt"


def test_file_given_multiple_times(tmp_path: Path) -> None:
    """
    Files given multiple times are de-duplicated.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    other_rst_file = tmp_path / "other_example.rst"
    content = """\
    .. code-block:: python

        block
    """
    other_content = """\
    .. code-block:: python

        other_block
    """
    rst_file.write_text(data=content, encoding="utf-8")
    other_rst_file.write_text(data=other_content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--command",
        "cat",
        str(object=rst_file),
        str(object=other_rst_file),
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        text="""\


        block


        other_block
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_verbose_running(tmp_path: Path) -> None:
    """
    Verbose output is shown showing what is running.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    content = """\
    .. code-block:: python

        x = 2 + 2
        assert x == 4

    .. skip doccmd[all]: next

    .. code-block:: python

        x = 3 + 3
        assert x == 6

    .. code-block:: shell

        echo 1
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--command",
        "cat",
        "--verbose",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        text="""\


        x = 2 + 2
        assert x == 4
        """,
    )
    expected_stderr = f"Running 'cat' on code block at {rst_file} line 1\n"
    expected_stderr = textwrap.dedent(
        text=f"""\
        Not using PTY for running commands.
        Running 'cat' on code block at {rst_file} line 1
        """,
    )
    assert result.stdout == expected_output
    assert result.stderr == expected_stderr


def test_verbose_not_utf_8(tmp_path: Path) -> None:
    """
    Verbose output shows what files are being skipped because they are not
    UTF-8.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    content = """\
    .. code-block:: python

       print("\xc0\x80")
    """
    rst_file.write_text(data=content, encoding="latin1")
    arguments = [
        "--verbose",
        "--language",
        "python",
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = ""
    assert result.stdout == expected_output
    # The first line here is not relevant, but we test the entire
    # verbose output to ensure that it is as expected.
    expected_stderr = textwrap.dedent(
        text=f"""\
            Not using PTY for running commands.
            Skipping '{rst_file}' because it is not UTF-8 encoded.
            """,
    )
    assert result.stderr == expected_stderr


def test_main_entry_point() -> None:
    """
    It is possible to run the main entry point.
    """
    result = subprocess.run(
        args=[sys.executable, "-m", "doccmd"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert "Usage:" in result.stderr


def test_command_not_found(tmp_path: Path) -> None:
    """
    An error is shown when the command is not found.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    non_existent_command = uuid.uuid4().hex
    non_existent_command_with_args = f"{non_existent_command} --help"
    content = """\
    .. code-block:: python

        x = 2 + 2
        assert x == 4
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--command",
        non_existent_command_with_args,
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code != 0
    expected_stderr = f"Error running command '{non_existent_command}':"
    assert result.stderr.startswith(expected_stderr)


def test_not_executable(tmp_path: Path) -> None:
    """
    An error is shown when the command is a non-executable file.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    not_executable_command = tmp_path / "non_executable"
    not_executable_command.touch()
    not_executable_command_with_args = (
        f"{not_executable_command.as_posix()} --help"
    )
    content = """\
    .. code-block:: python

        x = 2 + 2
        assert x == 4
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--command",
        not_executable_command_with_args,
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code != 0
    expected_stderr = "Error running command:"
    expected_stderr = (
        f"Error running command '{not_executable_command.as_posix()}':"
    )
    assert result.stderr.startswith(expected_stderr)


def test_multiple_languages(tmp_path: Path) -> None:
    """
    It is possible to run a command against multiple code blocks in a document
    with different languages.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    content = """\
    .. code-block:: python

        x = 2 + 2
        assert x == 4

    .. code-block:: javascript

        var y = 3 + 3;
        console.assert(y === 6);
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--no-pad-file",
        "--language",
        "python",
        "--language",
        "javascript",
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        text="""\
        x = 2 + 2
        assert x == 4
        var y = 3 + 3;
        console.assert(y === 6);
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_default_skip_rst(tmp_path: Path) -> None:
    """
    By default, the next code block after a 'doccmd skip: next' comment in a
    rST document is not run.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    content = """\
    .. code-block:: python

       block_1

    .. skip doccmd[all]: next

    .. code-block:: python

        block_2

    .. code-block:: python

        block_3
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--no-pad-file",
        "--language",
        "python",
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        text="""\
        block_1
        block_3
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_skip_no_arguments(tmp_path: Path) -> None:
    """
    An error is shown if a skip is given with no arguments.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    content = """\
    .. skip doccmd[all]:

    .. code-block:: python

        block_2
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--no-pad-file",
        "--language",
        "python",
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_stderr = (
        f"Skipping '{rst_file}' because it could not be parsed: "
        "Possibly a missing argument to a directive.\n"
    )

    assert result.stdout == ""
    assert result.stderr == expected_stderr


def test_skip_bad_arguments(tmp_path: Path) -> None:
    """
    An error is shown if a skip is given with bad arguments.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    content = """\
    .. skip doccmd[all]: !!!

    .. code-block:: python

        block_2
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--no-pad-file",
        "--language",
        "python",
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_stderr = (
        f"Skipping '{rst_file}' because it could not be parsed: "
        "malformed arguments to skip doccmd[all]: '!!!'\n"
    )

    assert result.stdout == ""
    assert result.stderr == expected_stderr


def test_custom_skip_markers_rst(tmp_path: Path) -> None:
    """
    The next code block after a custom skip marker comment in a rST document is
    not run.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    skip_marker = uuid.uuid4().hex
    content = f"""\
    .. code-block:: python

       block_1

    .. skip doccmd[{skip_marker}]: next

    .. code-block:: python

        block_2

    .. code-block:: python

        block_3
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--no-pad-file",
        "--language",
        "python",
        "--skip-marker",
        skip_marker,
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        text="""\
        block_1
        block_3
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_default_skip_myst(tmp_path: Path) -> None:
    """
    By default, the next code block after a 'doccmd skip: next' comment in a
    MyST document is not run.
    """
    runner = CliRunner(mix_stderr=False)
    myst_file = tmp_path / "example.md"
    content = """\
    Example

    ```python
    block_1
    ```

    <!--- skip doccmd[all]: next -->

    ```python
    block_2
    ```

    ```python
    block_3
    ```

    % skip doccmd[all]: next

    ```python
    block_4
    ```
    """
    myst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--no-pad-file",
        "--language",
        "python",
        "--command",
        "cat",
        str(object=myst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        text="""\
        block_1
        block_3
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_custom_skip_markers_myst(tmp_path: Path) -> None:
    """
    The next code block after a custom skip marker comment in a MyST document
    is not run.
    """
    runner = CliRunner(mix_stderr=False)
    myst_file = tmp_path / "example.md"
    skip_marker = uuid.uuid4().hex
    content = f"""\
    Example

    ```python
    block_1
    ```

    <!--- skip doccmd[{skip_marker}]: next -->

    ```python
    block_2
    ```

    ```python
    block_3
    ```

    % skip doccmd[{skip_marker}]: next

    ```python
    block_4
    ```
    """
    myst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--no-pad-file",
        "--language",
        "python",
        "--skip-marker",
        skip_marker,
        "--command",
        "cat",
        str(object=myst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        text="""\
        block_1
        block_3
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_multiple_skip_markers(tmp_path: Path) -> None:
    """
    All given skip markers, including the default one, are respected.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    skip_marker_1 = uuid.uuid4().hex
    skip_marker_2 = uuid.uuid4().hex
    content = f"""\
    .. code-block:: python

       block_1

    .. skip doccmd[{skip_marker_1}]: next

    .. code-block:: python

        block_2

    .. skip doccmd[{skip_marker_2}]: next

    .. code-block:: python

        block_3

    .. skip doccmd[all]: next

    .. code-block:: python

        block_4
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--no-pad-file",
        "--language",
        "python",
        "--skip-marker",
        skip_marker_1,
        "--skip-marker",
        skip_marker_2,
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        text="""\
        block_1
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_skip_start_end(tmp_path: Path) -> None:
    """
    Skip start and end markers are respected.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    skip_marker_1 = uuid.uuid4().hex
    skip_marker_2 = uuid.uuid4().hex
    content = """\
    .. code-block:: python

       block_1

    .. skip doccmd[all]: start

    .. code-block:: python

        block_2

    .. code-block:: python

        block_3

    .. skip doccmd[all]: end

    .. code-block:: python

        block_4
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--no-pad-file",
        "--language",
        "python",
        "--skip-marker",
        skip_marker_1,
        "--skip-marker",
        skip_marker_2,
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        text="""\
        block_1
        block_4
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_duplicate_skip_marker(tmp_path: Path) -> None:
    """
    Duplicate skip markers are respected.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    skip_marker = uuid.uuid4().hex
    content = f"""\
    .. code-block:: python

       block_1

    .. skip doccmd[{skip_marker}]: next

    .. code-block:: python

        block_2

    .. skip doccmd[{skip_marker}]: next

    .. code-block:: python

        block_3
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--no-pad-file",
        "--language",
        "python",
        "--skip-marker",
        skip_marker,
        "--skip-marker",
        skip_marker,
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        text="""\
        block_1
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_default_skip_marker_given(tmp_path: Path) -> None:
    """
    No error is shown when the default skip marker is given.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    skip_marker = "all"
    content = f"""\
    .. code-block:: python

       block_1

    .. skip doccmd[{skip_marker}]: next

    .. code-block:: python

        block_2

    .. skip doccmd[{skip_marker}]: next

    .. code-block:: python

        block_3
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--no-pad-file",
        "--language",
        "python",
        "--skip-marker",
        skip_marker,
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        text="""\
        block_1
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_skip_multiple(tmp_path: Path) -> None:
    """
    It is possible to mark a code block as to be skipped by multiple markers.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    skip_marker_1 = uuid.uuid4().hex
    skip_marker_2 = uuid.uuid4().hex
    content = f"""\
    .. code-block:: python

       block_1

    .. skip doccmd[{skip_marker_1}]: next
    .. skip doccmd[{skip_marker_2}]: next

    .. code-block:: python

        block_2
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--no-pad-file",
        "--language",
        "python",
        "--skip-marker",
        skip_marker_1,
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        text="""\
        block_1
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""

    arguments = [
        "--no-pad-file",
        "--language",
        "python",
        "--skip-marker",
        skip_marker_2,
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        text="""\
        block_1
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_bad_skips(tmp_path: Path) -> None:
    """
    Bad skip orders are flagged.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    skip_marker_1 = uuid.uuid4().hex
    content = f"""\
    .. skip doccmd[{skip_marker_1}]: end

    .. code-block:: python

        block_2
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--no-pad-file",
        "--language",
        "python",
        "--skip-marker",
        skip_marker_1,
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code != 0, (result.stdout, result.stderr)
    expected_stderr = textwrap.dedent(
        text="""\
        Error running command 'cat': 'skip: end' must follow 'skip: start'
        """,
    )

    assert result.stdout == ""
    assert result.stderr == expected_stderr


def test_empty_file(tmp_path: Path) -> None:
    """
    No error is shown when an empty file is given.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    rst_file.touch()
    arguments = [
        "--no-pad-file",
        "--language",
        "python",
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    assert result.stdout == ""
    assert result.stderr == ""


@pytest.mark.parametrize(
    argnames=("source_newline", "expect_crlf", "expect_cr", "expect_lf"),
    argvalues=[
        ("\n", False, False, True),
        ("\r\n", True, True, True),
        ("\r", False, True, False),
    ],
)
def test_detect_line_endings(
    *,
    tmp_path: Path,
    source_newline: str,
    expect_crlf: bool,
    expect_cr: bool,
    expect_lf: bool,
) -> None:
    """
    The line endings of the original file are used in the new file.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    content = """\
    .. code-block:: python

       block_1
    """
    rst_file.write_text(data=content, encoding="utf-8", newline=source_newline)
    arguments = [
        "--no-pad-file",
        "--language",
        "python",
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    assert result.stderr == ""
    assert bool(b"\r\n" in result.stdout_bytes) == expect_crlf
    assert bool(b"\r" in result.stdout_bytes) == expect_cr
    assert bool(b"\n" in result.stdout_bytes) == expect_lf


def test_one_supported_markup_in_another_extension(tmp_path: Path) -> None:
    """
    Code blocks in a supported markup language in a file with an extension
    which matches another extension are not run.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    content = """\
    ```python
    print("In simple markdown code block")
    ```

    ```{code-block} python
    print("In MyST code-block")
    ```
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--command",
        "cat",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    # Empty because the Markdown-style code block is not run in.
    expected_output = ""
    assert result.stdout == expected_output
    assert result.stderr == ""


@pytest.mark.parametrize(argnames="extension", argvalues=[".unknown", ""])
def test_unknown_file_suffix(extension: str, tmp_path: Path) -> None:
    """
    An error is shown when the file suffix is not known.
    """
    runner = CliRunner(mix_stderr=False)
    document_file = tmp_path / ("example" + extension)
    content = """\
    .. code-block:: python

        x = 2 + 2
        assert x == 4
    """
    document_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--command",
        "cat",
        str(object=document_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code != 0, (result.stdout, result.stderr)
    expected_stderr = textwrap.dedent(
        text=f"""\
            Usage: doccmd [OPTIONS] [DOCUMENT_PATHS]...
            Try 'doccmd --help' for help.

            Error: Markup language not known for {document_file}.
            """,
    )

    assert result.stdout == ""
    assert result.stderr == expected_stderr


def test_custom_rst_file_suffixes(tmp_path: Path) -> None:
    """
    ReStructuredText files with custom suffixes are recognized.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.customrst"
    content = """\
    .. code-block:: python

        x = 1
    """
    rst_file.write_text(data=content, encoding="utf-8")
    rst_file_2 = tmp_path / "example.customrst2"
    content_2 = """\
    .. code-block:: python

        x = 2
    """
    rst_file_2.write_text(data=content_2, encoding="utf-8")
    arguments = [
        "--no-pad-file",
        "--language",
        "python",
        "--command",
        "cat",
        "--rst-extension",
        ".customrst",
        "--rst-extension",
        ".customrst2",
        str(object=rst_file),
        str(object=rst_file_2),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    expected_output = textwrap.dedent(
        text="""\
        x = 1
        x = 2
        """,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    assert result.stdout == expected_output
    assert result.stderr == ""


def test_custom_myst_file_suffixes(tmp_path: Path) -> None:
    """
    MyST files with custom suffixes are recognized.
    """
    runner = CliRunner(mix_stderr=False)
    myst_file = tmp_path / "example.custommyst"
    content = """\
    ```python
    x = 1
    ```
    """
    myst_file.write_text(data=content, encoding="utf-8")
    myst_file_2 = tmp_path / "example.custommyst2"
    content_2 = """\
    ```python
    x = 2
    ```
    """
    myst_file_2.write_text(data=content_2, encoding="utf-8")
    arguments = [
        "--no-pad-file",
        "--language",
        "python",
        "--command",
        "cat",
        "--myst-extension",
        ".custommyst",
        "--myst-extension",
        ".custommyst2",
        str(object=myst_file),
        str(object=myst_file_2),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    expected_output = textwrap.dedent(
        text="""\
        x = 1
        x = 2
        """,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    assert result.stdout == expected_output
    assert result.stderr == ""


@pytest.mark.parametrize(
    argnames=("options", "expected_output"),
    argvalues=[
        # We cannot test the actual behavior of using a pseudo-terminal,
        # as CI (e.g. GitHub Actions) does not support it.
        # Therefore we do not test the `--use-pty` option.
        (["--no-use-pty"], "stdout is not a terminal."),
        # We are not really testing the detection mechanism.
        (["--detect-use-pty"], "stdout is not a terminal."),
    ],
    ids=["no-use-pty", "detect-use-pty"],
)
def test_pty(
    tmp_path: Path,
    options: Sequence[str],
    expected_output: str,
) -> None:
    """
    Test options for using pseudo-terminal.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    tty_test = textwrap.dedent(
        text="""\
        import sys

        if sys.stdout.isatty():
            print("stdout is a terminal.")
        else:
            print("stdout is not a terminal.")
        """,
    )
    script = tmp_path / "my_script.py"
    script.write_text(data=tty_test)
    script.chmod(mode=stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    content = """\
    .. code-block:: python

       block_1
    """
    rst_file.write_text(data=content, encoding="utf-8")
    arguments = [
        *options,
        "--no-pad-file",
        "--language",
        "python",
        "--command",
        f"{Path(sys.executable).as_posix()} {script.as_posix()}",
        str(object=rst_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    assert result.stderr == ""
    assert result.stdout.strip() == expected_output


@pytest.mark.parametrize(
    argnames="option",
    argvalues=["--rst-extension", "--myst-extension"],
)
def test_source_given_extension_no_leading_period(
    tmp_path: Path,
    option: str,
) -> None:
    """
    An error is shown when a given source file extension is given with no
    leading period.
    """
    runner = CliRunner(mix_stderr=False)
    source_file = tmp_path / "example.rst"
    content = "Hello world"
    source_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--command",
        "cat",
        option,
        "customrst",
        str(object=source_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code != 0, (result.stdout, result.stderr)
    expected_stderr = textwrap.dedent(
        text=f"""\
            Usage: doccmd [OPTIONS] [DOCUMENT_PATHS]...
            Try 'doccmd --help' for help.

            Error: Invalid value for '{option}': 'customrst' does not start with a '.'.
            """,  # noqa: E501
    )
    assert result.stdout == ""
    assert result.stderr == expected_stderr


def test_overlapping_extensions(tmp_path: Path) -> None:
    """
    An error is shown if there are overlapping extensions between --rst-
    extension and --myst-extension.
    """
    runner = CliRunner(mix_stderr=False)
    source_file = tmp_path / "example.custom"
    content = """\
    .. code-block:: python

        x = 1
    """
    source_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--command",
        "cat",
        "--rst-extension",
        ".custom",
        "--myst-extension",
        ".custom",
        "--rst-extension",
        ".custom2",
        "--myst-extension",
        ".custom2",
        str(object=source_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code != 0, (result.stdout, result.stderr)
    expected_stderr = textwrap.dedent(
        text="""\
            Usage: doccmd [OPTIONS] [DOCUMENT_PATHS]...
            Try 'doccmd --help' for help.

            Error: Overlapping suffixes between MyST and reStructuredText: .custom, .custom2.
            """,  # noqa: E501
    )
    assert result.stdout == ""
    assert result.stderr == expected_stderr


def test_overlapping_extensions_dot(tmp_path: Path) -> None:
    """
    No error is shown if multiple extension types are '.'.
    """
    runner = CliRunner(mix_stderr=False)
    source_file = tmp_path / "example.custom"
    content = """\
    .. code-block:: python

        x = 1
    """
    source_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--no-pad-file",
        "--command",
        "cat",
        "--rst-extension",
        ".",
        "--myst-extension",
        ".",
        "--rst-extension",
        ".custom",
        str(object=source_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        text="""\
        x = 1
        """,
    )
    assert result.stdout == expected_output
    assert result.stderr == ""


def test_markdown(tmp_path: Path) -> None:
    """
    It is possible to run a command against a Markdown file.
    """
    runner = CliRunner(mix_stderr=False)
    source_file = tmp_path / "example.md"
    content = """\
    % skip doccmd[all]: next

    ```python
        x = 1
    ```

    <!--- skip doccmd[all]: next -->

    ```python
        x = 2
    ```

    ```python
        x = 3
    ```
    """
    source_file.write_text(data=content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--no-pad-file",
        "--command",
        "cat",
        "--rst-extension",
        ".",
        "--myst-extension",
        ".",
        "--markdown-extension",
        ".md",
        str(object=source_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_output = textwrap.dedent(
        text="""\
        x = 1
        x = 3
        """,
    )
    # The first skip directive is not run as "%" is not a valid comment in
    # Markdown.
    #
    # The second skip directive is run as `<!--- skip doccmd[all]:
    # next -->` is a valid comment in Markdown.
    #
    # The code block after the second skip directive is run as it is
    # a valid Markdown code block.
    assert result.stdout == expected_output
    assert result.stderr == ""


def test_directory(tmp_path: Path) -> None:
    """
    All source files in a given directory are worked on.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    rst_content = """\
    .. code-block:: python

       rst_1_block
    """
    rst_file.write_text(data=rst_content, encoding="utf-8")
    md_file = tmp_path / "example.md"
    md_content = """\
    ```python
    md_1_block
    ```
    """
    md_file.write_text(data=md_content, encoding="utf-8")
    sub_directory = tmp_path / "subdir"
    sub_directory.mkdir()
    rst_file_in_sub_directory = sub_directory / "subdir_example.rst"
    subdir_rst_content = """\
    .. code-block:: python

       rst_subdir_1_block
    """
    rst_file_in_sub_directory.write_text(
        data=subdir_rst_content,
        encoding="utf-8",
    )

    sub_directory_with_known_file_extension = sub_directory / "subdir.rst"
    sub_directory_with_known_file_extension.mkdir()

    arguments = [
        "--language",
        "python",
        "--no-pad-file",
        "--command",
        "cat",
        str(object=tmp_path),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr
    expected_output = textwrap.dedent(
        text="""\
        md_1_block
        rst_1_block
        rst_subdir_1_block
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_de_duplication_source_files_and_dirs(tmp_path: Path) -> None:
    """
    If a file is given which is within a directory that is also given, the file
    is de-duplicated.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    rst_content = """\
    .. code-block:: python

       rst_1_block
    """
    rst_file.write_text(data=rst_content, encoding="utf-8")
    sub_directory = tmp_path / "subdir"
    sub_directory.mkdir()
    rst_file_in_sub_directory = sub_directory / "subdir_example.rst"
    subdir_rst_content = """\
    .. code-block:: python

       rst_subdir_1_block
    """
    rst_file_in_sub_directory.write_text(
        data=subdir_rst_content,
        encoding="utf-8",
    )

    arguments = [
        "--language",
        "python",
        "--no-pad-file",
        "--command",
        "cat",
        str(object=tmp_path),
        str(object=sub_directory),
        str(object=rst_file_in_sub_directory),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr
    expected_output = textwrap.dedent(
        text="""\
        rst_1_block
        rst_subdir_1_block
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_max_depth(tmp_path: Path) -> None:
    """
    The --max-depth option limits the depth of directories to search for files.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    rst_content = """\
    .. code-block:: python

        rst_1_block
    """
    rst_file.write_text(data=rst_content, encoding="utf-8")

    sub_directory = tmp_path / "subdir"
    sub_directory.mkdir()
    rst_file_in_sub_directory = sub_directory / "subdir_example.rst"
    subdir_rst_content = """\
    .. code-block:: python

        rst_subdir_1_block
    """
    rst_file_in_sub_directory.write_text(
        data=subdir_rst_content,
        encoding="utf-8",
    )

    sub_sub_directory = sub_directory / "subsubdir"
    sub_sub_directory.mkdir()
    rst_file_in_sub_sub_directory = sub_sub_directory / "subsubdir_example.rst"
    subsubdir_rst_content = """\
    .. code-block:: python

        rst_subsubdir_1_block
    """
    rst_file_in_sub_sub_directory.write_text(
        data=subsubdir_rst_content,
        encoding="utf-8",
    )

    arguments = [
        "--language",
        "python",
        "--no-pad-file",
        "--command",
        "cat",
        "--max-depth",
        "1",
        str(object=tmp_path),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr
    expected_output = textwrap.dedent(
        text="""\
        rst_1_block
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""

    arguments = [
        "--language",
        "python",
        "--no-pad-file",
        "--command",
        "cat",
        "--max-depth",
        "2",
        str(object=tmp_path),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr
    expected_output = textwrap.dedent(
        text="""\
        rst_1_block
        rst_subdir_1_block
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""

    arguments = [
        "--language",
        "python",
        "--no-pad-file",
        "--command",
        "cat",
        "--max-depth",
        "3",
        str(object=tmp_path),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr
    expected_output = textwrap.dedent(
        text="""\
        rst_1_block
        rst_subdir_1_block
        rst_subsubdir_1_block
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_exclude_files_from_recursed_directories(tmp_path: Path) -> None:
    """
    Files with names matching the exclude pattern are not processed when
    recursing directories.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    rst_content = """\
    .. code-block:: python

        rst_1_block
    """
    rst_file.write_text(data=rst_content, encoding="utf-8")

    sub_directory = tmp_path / "subdir"
    sub_directory.mkdir()
    rst_file_in_sub_directory = sub_directory / "subdir_example.rst"
    subdir_rst_content = """\
    .. code-block:: python

        rst_subdir_1_block
    """
    rst_file_in_sub_directory.write_text(
        data=subdir_rst_content,
        encoding="utf-8",
    )

    excluded_file = sub_directory / "exclude_me.rst"
    excluded_content = """\
    .. code-block:: python

        excluded_block
    """
    excluded_file.write_text(data=excluded_content, encoding="utf-8")

    arguments = [
        "--language",
        "python",
        "--no-pad-file",
        "--command",
        "cat",
        "--exclude",
        "exclude_*e.*",
        str(object=tmp_path),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr
    expected_output = textwrap.dedent(
        text="""\
        rst_1_block
        rst_subdir_1_block
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_multiple_exclude_patterns(tmp_path: Path) -> None:
    """
    Files matching any of the exclude patterns are not processed when recursing
    directories.
    """
    runner = CliRunner(mix_stderr=False)
    rst_file = tmp_path / "example.rst"
    rst_content = """\
    .. code-block:: python

        rst_1_block
    """
    rst_file.write_text(data=rst_content, encoding="utf-8")

    sub_directory = tmp_path / "subdir"
    sub_directory.mkdir()
    rst_file_in_sub_directory = sub_directory / "subdir_example.rst"
    subdir_rst_content = """\
    .. code-block:: python

        rst_subdir_1_block
    """
    rst_file_in_sub_directory.write_text(
        data=subdir_rst_content,
        encoding="utf-8",
    )

    excluded_file_1 = sub_directory / "exclude_me.rst"
    excluded_content_1 = """\
    .. code-block:: python

        excluded_block_1
    """
    excluded_file_1.write_text(data=excluded_content_1, encoding="utf-8")

    excluded_file_2 = sub_directory / "ignore_me.rst"
    excluded_content_2 = """\
    .. code-block:: python

        excluded_block_2
    """
    excluded_file_2.write_text(data=excluded_content_2, encoding="utf-8")

    arguments = [
        "--language",
        "python",
        "--no-pad-file",
        "--command",
        "cat",
        "--exclude",
        "exclude_*e.*",
        "--exclude",
        "ignore_*e.*",
        str(object=tmp_path),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr
    expected_output = textwrap.dedent(
        text="""\
        rst_1_block
        rst_subdir_1_block
        """,
    )

    assert result.stdout == expected_output
    assert result.stderr == ""


def test_lexing_exception(tmp_path: Path) -> None:
    """
    Lexing exceptions are handled when an invalid source file is given.
    """
    runner = CliRunner(mix_stderr=False)
    source_file = tmp_path / "invalid_example.md"
    # Lexing error as there is a hyphen in the comment
    # or... because of the word code!
    invalid_content = """\
    <!-- code -->
    """
    source_file.write_text(data=invalid_content, encoding="utf-8")
    arguments = [
        "--language",
        "python",
        "--command",
        "cat",
        str(object=source_file),
    ]
    result = runner.invoke(
        cli=main,
        args=arguments,
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected_stderr = textwrap.dedent(
        text=(
            f"Skipping '{source_file}' because it could not be lexed: "
            "Could not find end of '    <!-- code -->\\n', starting at "
            "line 1, column 1, looking for '(?:(?<=\\n)    )?--+>' in "
            f"{source_file}:\n'    '.\n"
        ),
    )
    assert result.stderr == expected_stderr
