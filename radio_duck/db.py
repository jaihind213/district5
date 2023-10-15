import json
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
            raise InterfaceError(msg = f"[{connect_close_resource_msg}]: {self.__class__.__name__} already closed")
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


    def __init__(self, *args, **kwargs):
        self.host = kwargs.get("host", "specify_host")
        self.port = kwargs.get("port", 8000)
        self.scheme = kwargs.get("scheme", "http")
        self.timeout_sec = kwargs.get("timeout_sec", 10) # todo
        self.closed = False
        self.api = kwargs.get("api", "/v1/sql")
        if self.scheme == "http":
            self._http_connection = http.client.HTTPConnection(self.host, self.port, timeout=self.timeout_sec)
            try:
                self._http_connection.connect()
            except Exception as e:
                raise OperationalError(f"unable to connect to database: {e}") from e
        else:
            raise InterfaceError(msg = "driver only supports http scheme for now")

    def close(self):
        self._http_connection.close()
        self.closed = True

    @check_closed
    def commit(self):
        #for transaction. do everything in a single cursor operation. limited support at this time
        raise NotSupportedError(msg = "do everything in a single cursor execute. 'begin;......;commit();'")

    def rollback(self):
        # for transaction. do everything in a single cursor operation. limited support at this time
        raise NotSupportedError(msg = "do everything in a single cursor execute. 'begin;......;commit();'")

    @check_closed
    def cursor(self, *args, **kwargs):
        return Cursor(self, **kwargs)

    @property
    def http_connection(self):
        return self._http_connection


class Cursor(object):
    """
        A DB-API 2.0 (PEP 249) cursor.

        Do not create this object directly; use Connection.cursor().
    """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def __init__(self, connection: Connection):
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
        raise NotSupportedError(msg = "callproc not supported on cursor")

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
                :raise OperationalError if unable to execute query
                :raise ProgrammingError if query is empty or invalid or improper(ex: table not found)
        """
        if query is None or "" == query.strip():
            raise ProgrammingError(msg = "query is empty")

        request = {
            'sql': query,
            'timeout': self._connection.timeout_sec,
            'parameters': parameters
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        http_response = None
        response_status = -1
        response_payload = None

        try:
            request_payload = json.dumps(request)
            self._connection.http_connection.request('POST', self._connection.api, body=request_payload,
                                                     headers=headers)
            http_response = self._connection.http_connection.getresponse()
            response_status = http_response.status
            response_payload = http_response.read()
        except Exception as e:
            # todo: logging
            if response_status != -1:
                raise OperationalError(msg=f"failed to execute query. response status {response_status}. response: {response_payload}") from e
            raise OperationalError(msg=f"Failed to execute query {e}") from e
        finally:
            if http_response is not None:
                http_response.close()

        if response_status != 200:
            msg = f"failed to execute query. response status: {response_status}. response_payload: {response_payload}"
            if _is4xx(response_status):
                raise ProgrammingError(msg=msg)
            else:
                raise OperationalError(msg=msg)

        try:
            self._result = json.loads(response_payload.decode('utf-8'))
            self._index = 0
        except Exception as e:
            # todo logging
            raise OperationalError(msg=
                                   f"Failed to execute query. could not deserialize response: {e}.")


    def executemany(self, query: Union[bytes, str], seq_of_parameters) -> None:
        raise NotSupportedError(msg = "`executemany` is not supported, use `execute` instead")

    @check_closed
    def fetchone(self) -> Optional[tuple]:
        if self._result is None:
            raise ProgrammingError(msg = "cannot fetchone() before execute()")

        rows = self._result["rows"]
        if len(rows) == 0 or self._index < 0 or self._index >= len(rows):
            return None
        to_return = rows[self._index]
        self._index = self._index + 1
        return to_return

    @check_closed
    def fetchmany(self, size: Optional[int] = None) -> List[tuple]:
        if self._result is None:
            raise ProgrammingError(msg = "cannot fetchmany before execute()")
        if size is None or size <= 0:
            size = self._arraysize
        next_elements = self._result['rows'][self._index: self._index + size]
        self._index = self._index + size
        return next_elements

    @check_closed
    def fetchall(self) -> List[tuple]:
        if self._result is None:
            raise ProgrammingError(msg = "cannot fetchall before execute()")
        remaining = self._result["rows"][self._index:]
        self._index = len(self._result["rows"])
        return remaining

    def nextset(self):
        """Move to the next available result set (not supported)."""
        raise NotSupportedError(msg = "cursor.nextset")

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

        return self._get_description(columns_types, column_names)

    def _get_description(self, columns_types: List[str], column_names: List[str]) -> Any:
        return [(column_name, get_type_code(column_type), None, None, None, None, True) for
                column_name, column_type, in
                zip(column_names, columns_types)]

def _is4xx(status: int):
    return status >= 400 and status < 500