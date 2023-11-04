from sqlalchemy import types as alchemy_types

from radio_duck import db_types


def test_duckdb_to_alchemy_types():
    test_cases = {
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
        "DECIMAL": alchemy_types.FLOAT,
        "NUMERIC": alchemy_types.FLOAT,
        "DECIMAL(PREC, SCALE)": alchemy_types.DECIMAL,
        "HUGEINT": alchemy_types.BIGINT,
        "INTEGER": alchemy_types.Integer,
        "INT4": alchemy_types.Integer,
        "INT": alchemy_types.Integer,
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
        "UINTEGER": alchemy_types.INTEGER,
        "USMALLINT": alchemy_types.SMALLINT,
        "UTINYINT": alchemy_types.SMALLINT,
        "UUID": alchemy_types.String,
        "VARCHAR": alchemy_types.String,
        "CHAR": alchemy_types.String,
        "BPCHAR": alchemy_types.String,
        "TEXT": alchemy_types.String,
        "STRING": alchemy_types.String,
        "UBIGINT": alchemy_types.BIGINT,
    }
    for duckdb_type in test_cases:
        expected = test_cases[duckdb_type]
        assert expected == db_types.get_alchemy_type(duckdb_type)
        assert len(test_cases) == len(db_types._alchemy_type_map)
