import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Text, List, Set

from rasa.cli import utils as cli_utils

PLUGIN_PREFIX = "rasa-"


# noinspection PyProtectedMember
def add_plugin_parser(
    parser: argparse.ArgumentParser,
    subparsers: argparse._SubParsersAction,
    parents: List[argparse.ArgumentParser],
) -> None:
    _register_plugin_fallback(parser)
    _add_plugins_list_parser(subparsers, parents)


def _register_plugin_fallback(parser: argparse.ArgumentParser) -> None:
    current_error_fn = parser.error

    def command_not_found(message: Text) -> None:
        args = sys.argv
        if len(args) >= 2 and shutil.which(_executable_name(args)):
            _run_plugin(args)
        else:
            current_error_fn(message)

    # This patches only the outermost parser but that's enough for our purposes
    parser.error = command_not_found


def _executable_name(args: List[Text]) -> Text:
    return f"{PLUGIN_PREFIX}{args[1]}"


def _run_plugin(current_args: List[Text]) -> None:
    current_args[1] = _executable_name(current_args)
    current_args = current_args[1:]
    try:
        process = subprocess.run(current_args)
        sys.exit(process.returncode)
    except Exception as e:
        cli_utils.print_error(
            f"Something went wrong when executing the plugin "
            f"'{current_args[0]}'. Please make sure it is a valid "
            f"executable and uses the correct permissions. The "
            f"error was:\n{e}"
        )
        sys.exit(1)


def _add_plugins_list_parser(
    subparsers: argparse._SubParsersAction, parents: List[argparse.ArgumentParser]
) -> None:
    plugin_parsers = subparsers.add_parser(
        "plugins",
        parents=parents,
        help="List available Command-line plugins.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    plugin_parsers.set_defaults(func=list_plugins)


def list_plugins(_) -> None:
    """List all available command line plugins.

    Plugins are executables which are within $PATH and whose name starts with `rasa-`.
    """
    plugin_names = _plugin_executables()

    if not plugin_names:
        cli_utils.print_info("No command-line plugins were found.")
    else:
        formatted_plugins = "\n".join(
            [f"- {executable}" for executable in plugin_names]
        )
        cli_utils.print_info(
            f"The following command-line plugins were found:\n" f"{formatted_plugins}"
        )


def _plugin_executables() -> Set[Text]:
    paths = map(Path, os.getenv("PATH", "").split(os.pathsep))
    plugin_name = set()

    for p in paths:
        if p.is_dir():
            plugin_name |= {file.stem for file in p.glob(f"{PLUGIN_PREFIX}*")}
        elif p.is_file() and p.name.startswith(PLUGIN_PREFIX):
            plugin_name.update(p.stem)

    return plugin_name
