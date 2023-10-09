import json
from collections import namedtuple
from functools import wraps
import http.client
from typing import Union, Optional, List, Any

from radio_duck.db_types import get_type_code
from radio_duck.exceptions import NotSupportedError, InterfaceError, ProgrammingError, OperationalError, Error
from radio_duck import connect_close_resource_msg


def check_closed(f):
    """
    Decorator that checks if connection/cursor is closed.
    """

    @wraps(f)
    def g(self, *args, **kwargs):
        if self.closed:
            raise Error(f"[{connect_close_resource_msg}]: {self.__class__.__name__} already closed")
        return f(self, *args, **kwargs)

    return g


class Connection(object):
    """
       A DB-API 2.0 (PEP 249) connection.

       Do not create this object directly; use globals.connect().
    """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    # def __init__(self, host: str, port: int, api: str, scheme="http", timeout_sec=socket._GLOBAL_DEFAULT_TIMEOUT):
    #     self.host = host
    #     self.port = port
    #     self.scheme = scheme
    #     self.timeout_sec = timeout_sec
    #     self.closed = False
    #     self.api = api
    #     if scheme == "http":
    #         self._http_connection = http.client.HTTPConnection(host, port, timeout=timeout_sec)
    #     else:
    #         raise InterfaceError("driver only supports http scheme for now.")

    def __init__(self, *args, **kwargs):
        self.host = kwargs.get("host", "specify_host")
        self.port = kwargs.get("port", 8000)
        self.scheme = kwargs.get("scheme", "http")
        self.timeout_sec = kwargs.get("timeout_sec", 10) # todo
        self.closed = False
        self.api = kwargs.get("api", "/v1/sql")
        if self.scheme == "http":
            self._http_connection = http.client.HTTPConnection(self.host, self.port, timeout=self.timeout_sec)
        else:
            raise InterfaceError("driver only supports http scheme for now.")

    def close(self):
        self._http_connection.close()
        self.closed = True

    @check_closed
    def commit(self):
        #for transaction. do everything in a single cursor operation. limited support at this time
        raise NotSupportedError("do everything in a single cursor execute. 'begin;......;commit();'")

    def rollback(self):
        # for transaction. do everything in a single cursor operation. limited support at this time
        raise NotSupportedError("do everything in a single cursor execute. 'begin;......;commit();'")

    @check_closed
    def cursor(self, *args, **kwargs):
        return Cursor(self, **kwargs)

    @property
    def http_connection(self):
        return self._http_connection


CursorDescriptionRow = namedtuple(
    "CursorDescriptionRow",
    ["name", "type", "display_size", "internal_size", "precision", "scale", "null_ok"],
)

class Cursor(object):
    """
        A DB-API 2.0 (PEP 249) cursor.

        Do not create this object directly; use Connection.cursor().
    """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def __init__(self, connection: Connection, **kwargs):
        self.closed = False
        self._result = None
        self._connection = connection
        self._rowcount = -1
        self._arraysize = 1
        self._index = -1

    @property
    def connection(self) -> Connection:
        """
        Get the connection associated with this cursor.

        This is an optional DB-API extension.
        """
        return self._connection

    @property
    def rowcount(self):
        if self._result is None:
            return -1
        return len(self._result["rows"])

    def callproc(self, procname, *args):
        raise NotSupportedError()

    def close(self):
        # free up the resources
        self._result = None
        self._rowcount = -1
        self._index = -1
        self.closed = True

    @check_closed
    def execute(self, query: Union[bytes, str], parameters=None):
        """
                Execute a query.

                Parameters
                ----------
                query : bytes or str
                    The query to execute.  Pass SQL queries as strings,
                    (serialized) Substrait plans as bytes.
                parameters
                    Parameters to bind.  Can be a Python sequence (to provide
                    a single set of parameters).
                """
        if query is None or "" == query.strip():
            raise ProgrammingError("query is empty")

        request = {
            'sql': query,
            'timeout': self._connection.timeout_sec,
            'parameters': parameters
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        try:
            request_payload = json.dumps(request)
            self._connection.http_connection.request('POST', self._connection.api, body=request_payload,
                                                     headers=headers)
            response = self._connection.http_connection.getresponse()
            status = response.status
            response_data = response.read()
            if status == 200:
                self._result = json.loads(response_data.decode('utf-8'))
                self._index = 0
            else:
                raise OperationalError(
                    f"Failed to execute query. got response code {status}. response_payload: {response_data}")
        except Exception as e:
            # todo logging.
            raise OperationalError(f"Failed to execute query. {e}")

    def executemany(self, query: Union[bytes, str], seq_of_parameters) -> None:
        raise NotSupportedError("`executemany` is not supported, use `execute` instead")

    @check_closed
    def fetchone(self) -> Optional[tuple]:
        if self._result is None:
            raise ProgrammingError("Cannot fetchone() before execute()")

        rows = self._result["rows"]
        if len(rows) == 0 or self._index < 0 or self._index >= len(rows):
            return None
        to_return = rows[self._index]
        self._index = self._index + 1
        return to_return

    @check_closed
    def fetchmany(self, size: Optional[int] = None) -> List[tuple]:
        if self._result is None:
            raise ProgrammingError("Cannot fetchmany before execute()")
        if size is None or size <= 0:
            size = self._arraysize
        next_elements = self._result['rows'][self._index: self._index + size]
        self._index = self._index + size
        return next_elements

    @check_closed
    def fetchall(self) -> List[tuple]:
        if self._result is None:
            raise ProgrammingError("Cannot fetchall before execute()")
        remaining = self._result["rows"][self._index:]
        self._index = len(self._result["rows"])
        return remaining

    def nextset(self):
        """Move to the next available result set (not supported)."""
        raise NotSupportedError("Cursor.nextset")

    @property
    def arraysize(self):
        return self._arraysize

    @arraysize.setter
    def arraysize(self, size):
        self._arraysize = size

    def setinputsizes(self, sizes):
        """Preallocate memory for the parameters (no-op)."""
        pass

    def setoutputsize(self, size, column=None):
        """Preallocate memory for the result set (no-op)."""
        pass

    @property
    def description(self):
        """
        This read-only attribute is a sequence of 7-item sequences.
        """
        if self.closed or self._result is None:
            return None

        columns_types = self._result.get("schema", [])
        column_names = self._result.get("columns", [])

        return self.__get_description(columns_types, column_names)

    def __get_description(self, columns_types: List[str], column_names: List[str]) -> Any:
        desc = [(column_name, get_type_code(column_type), None, None, None, None, True) for
                column_name, column_type, in
                zip(column_names, columns_types)]
        return tuple(desc)
        #return desc
