# https://peps.python.org/pep-0249/#exceptions

class Error(Exception):
    def __init__(self, *args, msg="", **kwargs):
        self.msg = msg


class Warning(Exception):
    def __init__(self, *args, msg="", **kwargs):
        self.msg = msg


class InterfaceError(Error):
    def __init__(self, *args, msg="", **kwargs):
        self.msg = msg


class DatabaseError(Error):
    pass


class InternalError(DatabaseError):
    pass


class OperationalError(DatabaseError):
    def __init__(self, *args, msg="", **kwargs):
        self.msg = msg


class ProgrammingError(DatabaseError):
    def __init__(self, *args, msg="", **kwargs):
        self.msg = msg


class IntegrityError(DatabaseError):
    pass


class DataError(DatabaseError):
    pass


class NotSupportedError(DatabaseError):
    def __init__(self, *args, msg="", **kwargs):
        self.msg = msg

__all__ = ['Error', 'DataError', 'ProgrammingError',
           'IntegrityError', 'InterfaceError',
           'OperationalError', 'InternalError',
           'DatabaseError', 'NotSupportedError']