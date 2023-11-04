# https://peps.python.org/pep-0249/#globals

from typing import Any

from radio_duck.db import Connection

apilevel = "2.0"

threadsafety = 1

paramstyle = "qmark"

__all__ = ["apilevel", "threadsafety", "paramstyle", "connect"]


# ----------------------------------------------------------
# Functions


def connect(*args, **kwargs) -> Any:
    """
    Connect to the database
    :param args:
    :param kwargs: minimum kwargs are host,port,
    api(endpoint url ex: '/v1/sql'). optional: timeout_sec
    :return: Connection object
    :raise ProgrammingError on incorrect scheme
    :raise OperationalError if unable to connect to database
    """
    return Connection(*args, **kwargs)
