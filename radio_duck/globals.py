#https://peps.python.org/pep-0249/#globals

from typing import Any

from radio_duck.db import Connection

apilevel = "2.0"

threadsafety = 1

paramstyle = "qmark"

__all__ = ['apilevel', 'threadsafety', 'paramstyle', 'connect']

# ----------------------------------------------------------
# Functions

def connect(*args, **kwargs) -> Any:
    return Connection(*args, **kwargs)
