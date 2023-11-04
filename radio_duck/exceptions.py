# https://peps.python.org/pep-0249/#exceptions


class Error(Exception):
    def __init__(self, *args, **kwargs):
        self.msg = kwargs.get("msg", "")
        self.response_status = kwargs.get("response_status", -1)

    def __str__(self):
        details = "" if self.__cause__ is None else repr(self.__cause__)
        return (
            f"radio_duck_error: msg {self.msg}, "
            f"response_status: {self.response_status}. "
            f"details: {details}"
        )


class Warning(Exception):
    def __init__(self, *args, **kwargs):
        self.msg = kwargs.get("msg", "")


class InterfaceError(Error):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class DatabaseError(Error):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class InternalError(DatabaseError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class OperationalError(DatabaseError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ProgrammingError(DatabaseError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class IntegrityError(DatabaseError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class DataError(DatabaseError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class NotSupportedError(DatabaseError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


__all__ = [
    "Error",
    "DataError",
    "ProgrammingError",
    "IntegrityError",
    "InterfaceError",
    "OperationalError",
    "InternalError",
    "DatabaseError",
    "NotSupportedError",
]
