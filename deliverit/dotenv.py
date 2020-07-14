from typing import *
from pathlib import Path
from os import getenv

from dotenv import load_dotenv

from deliverit.context import Context
from deliverit.ui import MESSAGE_NO_VALID_DOTENV_FILE


def load(ctx: Context):
    #TODO: configurable .env filepath thru credentials: 
    #that's why `ctx` is passed
    if not Path(".env").is_file():
        raise FileNotFoundError(MESSAGE_NO_VALID_DOTENV_FILE)

    load_dotenv(".env")

    if not all(
        (getenv("GITHUB_TOKEN"), getenv("PYPI_USERNAME"), getenv("PYPI_PASSWORD"))
    ):
        raise ValueError(MESSAGE_NO_VALID_DOTENV_FILE)
