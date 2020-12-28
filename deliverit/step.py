from __future__ import annotations
from typing import Union, Optional, Any
import subprocess
from os import getenv

import deliverit.config
from deliverit.ui import *


def make_step_function(
    args: dict[str, Any], config: deliverit.config.Configuration
) -> Callable:
    def step(
        id: str,
        message: str,
        action: Optional[Callable] = None,
        command: Optional[Union[str, tuple[str]]] = None,
        commands: Optional[list[Union[str, tuple[str]]]] = None,
        cancellable: bool = True,
        nonzero_ok: bool = False,
    ) -> Any:
        if id in args["--disable-step"] or not getattr(config.steps, id):
            return
        if command:
            commands = [command]
        if action is None and command is None:
            return TypeError("'action' and 'command' cannot be both None")
        print("")
        print(dim(b(message)))
        if commands:
            for command in commands:
                print(
                    dim("$ ")
                    + em(
                        (
                            " ".join(command)
                            if type(command) in (list, tuple)
                            else command
                        )
                        .replace(str(getenv("PYPI_PASSWORD")), "[HIDDEN]")
                        .replace(str(getenv("GITHUB_TOKEN")), "[HIDDEN]")
                    )
                )
        if not args["--yes"] and cancellable:
            try:
                answer = input(
                    dim("Press ")
                    + b("⏎")
                    + dim(" to confirm or ")
                    + b("Ctrl-C")
                    + dim(" to cancel")
                )
                print()
                erase_previous_line()
                erase_previous_line()
                if answer == "S":
                    return
            except KeyboardInterrupt:
                print_on_same_line("Cancelled.")
                exit(1)
        if not args["--dry-run"]:
            if commands:
                for command in commands:
                    proc = subprocess.run(  # pylint: disable=subprocess-run-check
                        command,
                        capture_output=not args["--verbose"],
                        shell=type(command) is str,
                    )
                    if proc.returncode != 0 and not nonzero_ok:
                        print(
                            red("An error occured while running the command ")
                            + dim(red(f"(it returned {proc.returncode})"))
                            + red(". Here's its output...")
                        )
                        print(red("- on stderr"))
                        print(proc.stderr.decode("utf-8"))
                        print(red("- on stdout"))
                        print(proc.stdout.decode("utf-8"))
            else:
                return action()
        elif args["--verbose"]:
            print(dim("(dry run)"))

    return step
