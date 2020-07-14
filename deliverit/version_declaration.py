import re
from typing import *
from pathlib import Path

from deliverit.context import Context
import deliverit.config

def update(
    ctx: Context, declaration: deliverit.config.VersionDeclaration,
):
    updated_contents = ""
    filepath = ctx.apply(declaration.in_)
    current_contents = Path(filepath).read_text("utf-8")
    for line in current_contents.splitlines():
        if re.match(declaration.search, line):
            updated_contents += ctx.apply(declaration.replace) + "\n"
        else:
            updated_contents += f"{line}\n"
    Path(filepath).write_text(updated_contents)
