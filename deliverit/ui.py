"""
Functions related to UI
Mostly shortcuts for termcolor
"""

from typing import *
import sys

from termcolor import colored

red = lambda s: colored(s, "red")
green = lambda s: colored(s, "green")
em = lambda s: colored(s, "cyan", attrs=("bold",))
b = lambda s: colored(s, attrs=("bold",))
reset = lambda s: colored(s, "white")
dim = lambda s: colored(s, attrs=("dark",))
warn = lambda s: colored(s, "yellow", attrs=("dark",))


def erase_previous_line():
    sys.stdout.write("\033[K")
    sys.stdout.write("\033[F")


def print_on_same_line(mesage: str, *args, **kwargs):
    erase_previous_line()
    print(mesage, *args, **kwargs)


MESSAGE_NO_VALID_DOTENV_FILE = """\
Add a .env file to this directory with the following contents:

    GITHUB_TOKEN="your github personnal access token"
    PYPI_USERNAME="your PyPI account username"
    PYPI_PASSWORD="your PyPI account's password"

⚠ MAKE SURE TO .GITIGNORE THIS FILE BEFORE RUNNING THE COMMAND AGAIN.
  IF THIS FILE IS NOT IGNORED, IT COULD BE UPLOADED, AND ACCESS TO YOUR
  GITHUB *AND* PYPI ACCOUNTS WOULD BE MADE PUBLIC
"""
