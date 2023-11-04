import datetime
import time

from sqlalchemy import types as alchemy_types

# ----------------------------------------------------------
# Types

#: The type for date values.
Date = datetime.date
#: The type for time values.
Time = datetime.time
#: The type for timestamp values.
Timestamp = datetime.datetime


def Binary(string):
    return str(string)


def DateFromTicks(ticks: int) -> Date:
    """Construct a date value from a count of seconds."""
    # Standard implementations from PEP 249 itself
    return Date(*time.localtime(ticks)[:3])


def TimeFromTicks(ticks: int) -> Time:
    """Construct a time value from a count of seconds."""
    return Time(*time.localtime(ticks)[3:6])


def TimestampFromTicks(ticks: int) -> Timestamp:
    """Construct a timestamp value from a count of seconds."""
    return Timestamp(*time.localtime(ticks)[:6])


class Type(object):
    def __init__(self, type_code: int):
        self._type_code = type_code

    def get_type_code(self):
        return self._type_code


# use the 5 ducks
# from https://disney.fandom.com/wiki/District_5_Ducks
# using jersey numbers :)
STRING = Type(96)  # one of 5 ducks in flying v -charlie convay.
BINARY = Type(4)  # one of 5 ducks in flying v -averman
NUMBER = Type(9)  # one of 5 ducks in flying v -jesse hall.
DATETIME = Type(1)  # one of 5 ducks in flying v -Terry Hall
ROWID = Type(0)  # one of 5 ducks in flying v -Guy Germaine
UNKNOWN = Type(-1)  # one of 5 ducks in flying v -Guy Germaine

__types = {
    "STRING": STRING,
    "BINARY": BINARY,
    "NUMBER": NUMBER,
    "DATETIME": DATETIME,
    "ROWID": ROWID,
}


def get_type_code(col_type: str) -> int:
    return __types.get(col_type, UNKNOWN).get_type_code()


# ----------------------------------------------------------


# https://github.com/preset-io/elasticsearch-dbapi/blob/master/es/baseapi.py

_alchemy_type_map = {
    "BIGINT": alchemy_types.BIGINT,
    "INT8": alchemy_types.BIGINT,
    "LONG": alchemy_types.BIGINT,
    "BIT": alchemy_types.String,
    "BITSTRING": alchemy_types.String,
    "BOOLEAN": alchemy_types.Boolean,
    "BOOL": alchemy_types.Boolean,
    "LOGICAL": alchemy_types.Boolean,
    "BLOB": alchemy_types.BLOB,
    "BYTEA": alchemy_types.BLOB,
    "BINARY": alchemy_types.BLOB,
    "VARBINARY": alchemy_types.BLOB,
    "DATE": alchemy_types.DATE,
    "DOUBLE": alchemy_types.FLOAT,
    "FLOAT8": alchemy_types.FLOAT,
    "NUMERIC": alchemy_types.FLOAT,
    "DECIMAL": alchemy_types.FLOAT,
    "DECIMAL(PREC, SCALE)": alchemy_types.DECIMAL,
    "HUGEINT": alchemy_types.BIGINT,
    "INTEGER": alchemy_types.Integer,
    "INT": alchemy_types.Integer,
    "INT4": alchemy_types.Integer,
    "SIGNED": alchemy_types.Integer,
    "INTERVAL": alchemy_types.Interval,
    "REAL": alchemy_types.FLOAT,
    "FLOAT4": alchemy_types.FLOAT,
    "FLOAT": alchemy_types.FLOAT,
    "SMALLINT": alchemy_types.SMALLINT,
    "INT2": alchemy_types.SMALLINT,
    "SHORT": alchemy_types.SMALLINT,
    "TIME": alchemy_types.TIME,
    "TIMESTAMP": alchemy_types.TIMESTAMP,
    "DATETIME": alchemy_types.TIMESTAMP,
    "TIMESTAMP WITH TIME ZONE": alchemy_types.TIMESTAMP,
    "TIMESTAMPTZ": alchemy_types.TIMESTAMP,
    "TINYINT": alchemy_types.SMALLINT,
    "INT1": alchemy_types.SMALLINT,
    "UBIGINT": alchemy_types.BIGINT,
    "UINTEGER": alchemy_types.INTEGER,
    "USMALLINT": alchemy_types.SMALLINT,
    "UTINYINT": alchemy_types.SMALLINT,
    "UUID": alchemy_types.String,
    "STRING": alchemy_types.String,
    "TEXT": alchemy_types.String,
    "BPCHAR": alchemy_types.String,
    "CHAR": alchemy_types.String,
    "VARCHAR": alchemy_types.String,
}


def get_alchemy_type(data_type):
    if "[]" in data_type:  # LIST
        return alchemy_types.ARRAY
    elif "UNION" in data_type or "STRUCT" in data_type or "MAP" in data_type:
        return alchemy_types.BLOB  # other complex
    else:
        return _alchemy_type_map[data_type.upper()]
