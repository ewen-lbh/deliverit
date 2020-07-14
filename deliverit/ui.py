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
