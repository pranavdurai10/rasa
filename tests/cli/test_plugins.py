import os
import sys
from pathlib import Path
from typing import Text

import pytest
from _pytest.monkeypatch import MonkeyPatch
from _pytest.pytester import Testdir

from rasa.cli.plugins import PLUGIN_PREFIX

EXPECTED_PLUGIN_OUTPUT = "Hello Rasa plugin"


@pytest.fixture()
def example_plugin() -> Text:
    if sys.platform == "win32":
        return f"""echo on
echo "{EXPECTED_PLUGIN_OUTPUT}" """
    else:
        return f"""#!/bin/bash
echo "{EXPECTED_PLUGIN_OUTPUT}" """


def _install_plugin(
    script_content: Text,
    plugin_name: Text,
    plugin_directory: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    plugin_path = plugin_directory / f"{PLUGIN_PREFIX}{plugin_name}"
    plugin_path.write_text(script_content)
    plugin_path.chmod(0o777)

    monkeypatch.setenv("PATH", f"{os.getenv('PATH')}:{str(plugin_directory)}")


def test_plugin_execution(
    testdir: Testdir, tmp_path: Path, example_plugin: Text, monkeypatch: MonkeyPatch
):
    plugin_name = "hello"

    _install_plugin(example_plugin, plugin_name, tmp_path, monkeypatch)

    result = testdir.run("rasa", plugin_name)
    assert result.ret == 0
    assert result.outlines[0] == EXPECTED_PLUGIN_OUTPUT


def test_plugin_with_script_error(
    testdir: Testdir, monkeypatch: MonkeyPatch, tmp_path: Path
):
    plugin_script = """#!/bin/basdadssh
echo "bla"
    """

    plugin_name = "hello"
    _install_plugin(plugin_script, plugin_name, tmp_path, monkeypatch)

    result = testdir.run("rasa", plugin_name)
    assert result.ret != 0

    assert result.outlines


def test_list_plugins(
    testdir: Testdir, tmp_path: Path, example_plugin: Text, monkeypatch: MonkeyPatch
):
    available_plugins = ["hello", "forum"]
    for plugin_name in available_plugins:
        _install_plugin(example_plugin, plugin_name, tmp_path, monkeypatch)

    result = testdir.run("rasa", "plugins")

    assert result.ret == 0

    cmd_output = "\n".join(result.outlines)
    assert all(plugin_name in cmd_output for plugin_name in available_plugins)


def test_list_plugins_without_any_plugin(testdir: Testdir,):
    result = testdir.run("rasa", "plugins")

    assert result.ret == 0

    cmd_output = "\n".join(result.outlines)
    assert "No command-line plugins were found" in cmd_output
