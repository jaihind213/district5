from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import sqlalchemy

from radio_duck.reserved_keywords import keyword_list

if TYPE_CHECKING:
    from _typeshed import DBAPIConnection

from typing import Any, Callable, List

# https://docs.sqlalchemy.org/en/20/core/internals.html#sqlalchemy.engine.Dialect.do_terminate
# from sqlalchemy.engine import default, interfaces
from sqlalchemy.engine import default
from sqlalchemy.sql import compiler

import radio_duck
from radio_duck import db_types
from radio_duck.db import connect_close_resource_msg
from radio_duck.exceptions import NotSupportedError
from radio_duck.queries import (
    get_columns,
    get_constraints,
    get_indexes,
    get_schemas,
    get_sequences,
    get_tables,
    get_temp_tables,
    get_temp_views,
    get_view_sql,
    get_views,
    has_index_query,
    has_sequence_query,
    has_table_query,
)


class RadioDuckDialectPreparer(compiler.IdentifierPreparer):
    reserved_words = keyword_list


class RadioDuckDialectTypeCompiler(compiler.GenericTypeCompiler):
    """
    Refer
    https://duckdb.org/docs/sql/data_types/numeric
    https://duckdb.org/docs/sql/data_types/overview.html
    https://www.postgresql.org/docs/current/datatype-numeric.html
    """

    visit_REAL = compiler.GenericTypeCompiler.visit_FLOAT
    visit_NUMERIC = compiler.GenericTypeCompiler.visit_DECIMAL

    visit_DATETIME = compiler.GenericTypeCompiler.visit_TIMESTAMP

    visit_CLOB = compiler.GenericTypeCompiler.visit_BLOB
    visit_NCLOB = compiler.GenericTypeCompiler.visit_BLOB
    visit_BINARY = compiler.GenericTypeCompiler.visit_BLOB
    visit_VARBINARY = compiler.GenericTypeCompiler.visit_BLOB

    visit_TEXT = compiler.GenericTypeCompiler.visit_VARCHAR


class RadioDuckDialect(default.DefaultDialect):
    type_compiler = RadioDuckDialectTypeCompiler
    preparer = RadioDuckDialectPreparer

    supports_sequences = True
    supports_native_enum = True
    supports_native_boolean = True

    tuple_in_values = True

    # if the NUMERIC type
    # returns decimal.Decimal.
    # *not* the FLOAT type however.
    supports_native_decimal = True

    name = "radio_duck"
    driver = "district5"

    isolation_level = "SNAPSHOT"

    default_paramstyle = "qmark"

    # not sure if this is a real thing but the compiler will deliver it
    # if this is the only flag enabled.
    supports_empty_insert = False
    """dialect supports INSERT () VALUES ()"""

    supports_multivalues_insert = True

    default_schema_name = "main"  # duckdb default schema is main

    @classmethod
    def dbapi(cls):
        return radio_duck

    def __init__(
        self,
        convert_unicode=False,
        encoding="utf-8",
        paramstyle=None,
        dbapi=None,
        implicit_returning=None,
        case_sensitive=True,
        supports_native_boolean=None,
        max_identifier_length=None,
        label_length=None,
        # int() is because the @deprecated_params decorator cannot accommodate
        # the direct reference to the "NO_LINTING" object
        compiler_linting=int(compiler.NO_LINTING),  # noqa: B008
        server_side_cursors=False,
        **kwargs,
    ):
        super().__init__(
            convert_unicode=convert_unicode,
            encoding=encoding,
            paramstyle=paramstyle,
            dbapi=dbapi,
            implicit_returning=implicit_returning,
            case_sensitive=case_sensitive,
            supports_native_boolean=supports_native_boolean,
            max_identifier_length=max_identifier_length,
            label_length=label_length,
            compiler_linting=compiler_linting,
            server_side_cursors=server_side_cursors,
            **kwargs,
        )

    # do methods

    def do_savepoint(self, connection, name):
        raise NotImplementedError()

    def do_rollback_to_savepoint(self, connection, name):
        raise NotImplementedError()

    def do_rollback(self, dbapi_connection):
        pass
        # raise NotImplementedError()

    def do_release_savepoint(self, connection, name):
        raise NotImplementedError()

    def do_recover_twophase(self, connection):
        raise NotImplementedError()

    def do_prepare_twophase(self, connection, xid):
        raise NotImplementedError()

    def do_commit_twophase(
        self, connection, xid, is_prepared=True, recover=False
    ):
        raise NotImplementedError()

    def do_commit(self, dbapi_connection):
        pass

    def do_begin_twophase(self, connection, xid) -> None:
        raise NotImplementedError()

    def do_begin(self, dbapi_connection):
        pass

    # -- connect methods

    def create_connect_args(self, url):
        """Build DB-API compatible connection arguments.
        :param url: a :class:`.URL` object

        :return: a tuple of ``(*args, **kwargs)`` which will be passed to the
         :meth:`.Dialect.connect` method.

        .. seealso::    :meth:`.URL.translate_connect_args`
        """

        opts = url.translate_connect_args()
        opts.update(url.query)
        # todo: default impl returns [[], opts]..
        # this is a bug as pydoc says return tuple! not list
        return [], opts

    def create_xid(self):
        raise NotSupportedError("transactions not supported over http yet")

    @classmethod
    def engine_created(cls, engine):
        super().engine_created(engine)
        logging.info("radio_duck dialect engine created")

    def reset_isolation_level(self, dbapi_conn) -> None:
        pass

    def set_isolation_level(self, dbapi_conn, level) -> None:
        pass

    def on_connect(self) -> Callable[[DBAPIConnection], object] | None:
        def do_on_connect(connection):
            # todo. set duckdb specific flags
            # connection.execute("SET SPECIAL FLAGS etc")
            logging.debug("radio_duck pre connection  establishment hook.")

        return do_on_connect

    def on_connect_url(
        self, url
    ) -> Callable[[DBAPIConnection], object] | None:
        def do_on_connect_url(connection):
            # todo. set duckdb specific flags
            # connection.execute("SET SPECIAL FLAGS etc")
            logging.debug(
                "radio_duck pre connection establishment hook to url: ", url
            )

        return do_on_connect_url

    def is_disconnect(self, e, connection, cursor):
        """
            Return True if the given DB-API error
            indicates an invalid connection
        :param e:
        :param connection:
        :param cursor:
        :return:
        """
        # return all(
        #     e is not None,
        #     radio_duck.db.connect_close_resource_msg in str(e)
        # )
        return False if e is None else connect_close_resource_msg in str(e)

    # ----has methods

    def has_index(self, connection, table_name, index_name, schema=None):
        if schema is None or "" == schema.strip():
            schema = RadioDuckDialect.default_schema_name
        rows = self._execute_query(
            connection, has_index_query, schema, table_name, index_name
        )
        return len(rows) == 1

    def has_table(self, connection, table_name, schema=None, **kw) -> None:
        if schema is None or "" == schema.strip():
            schema = RadioDuckDialect.default_schema_name
        rows = self._execute_query(
            connection, has_table_query, schema, table_name
        )
        return len(rows) == 1

    def has_sequence(
        self, connection, sequence_name, schema=None, **kw
    ) -> bool:
        if schema is None or "" == schema.strip():
            schema = RadioDuckDialect.supports_schemas
        rows = self._execute_query(
            connection, has_sequence_query, schema, sequence_name
        )
        return len(rows) == 1

    # ----get methods

    def get_table_names(
        self, connection, schema=None, **kw
    ) -> List[str] | None:
        if schema is None or "" == schema.strip():
            schema = RadioDuckDialect.default_schema_name

        rows = self._execute_query(
            connection, get_tables, schema
        )  # list of list
        table_names = [col_val for row in rows for col_val in row]
        return table_names

    def get_view_names(self, connection, schema=None, **kw):
        if schema is None or "" == schema.strip():
            schema = RadioDuckDialect.default_schema_name
        rows = self._execute_query(
            connection, get_views, schema
        )  # list of list
        views = [col_val for row in rows for col_val in row]
        return views

    def get_view_definition(
        self, connection, view_name, schema=None, **kw
    ) -> None:
        if schema is None or "" == schema.strip():
            schema = RadioDuckDialect.default_schema_name
        rows = self._execute_query(connection, get_view_sql, schema, view_name)
        if len(rows) == 0:
            return ""
        row = rows[0]
        return row[0]  # return sql

    def get_unique_constraints(
        self, connection, table_name, schema=None, **kw
    ) -> list[dict[str, Any]]:
        if schema is None or "" == schema.strip():
            schema = RadioDuckDialect.default_schema_name

        rows = self._execute_query(
            connection, get_constraints, schema, table_name, "UNIQUE"
        )  # list of list
        list_of_maps = [
            {"name": row[0], "column_names": row[1]} for row in rows
        ]
        return list_of_maps

    def get_temp_view_names(self, connection, schema=None, **kw):
        # Temporary views exist in a special schema, so a schema name
        # cannot be given when creating a temporary view.
        # The name of the view must be distinct from the name of any
        # other view or table in the same schema.
        # hence schema is ignored for query
        rows = self._execute_query(connection, get_temp_views)  # list of list
        temp_views = [col_val for row in rows for col_val in row]
        return temp_views

    def get_temp_table_names(self, connection, schema=None, **kw):
        if schema is None or "" == schema.strip():
            schema = RadioDuckDialect.default_schema_name

        rows = self._execute_query(
            connection, get_temp_tables, schema
        )  # list of list
        temp_tables = [col_val for row in rows for col_val in row]
        return temp_tables

    def get_table_comment(self, connection, table_name, schema=None, **kw):
        raise NotImplementedError()

    def get_sequence_names(self, connection, schema=None, **kw) -> list[Any]:
        if schema is None or "" == schema.strip():
            schema = RadioDuckDialect.default_schema_name
        rows = self._execute_query(
            connection, get_sequences, schema
        )  # list of list
        seq_names = [col_val for row in rows for col_val in row]
        return seq_names

    def get_pk_constraint(self, connection, table_name, schema=None, **kw):
        if schema is None or "" == schema.strip():
            schema = RadioDuckDialect.default_schema_name

        rows = self._execute_query(
            connection, get_constraints, schema, table_name, "PRIMARY KEY"
        )  # list of list
        if len(rows) == 0:
            return []
        row = rows[0]
        list_of_maps = (
            [{"name": row[0], "column_names": row[1]}]
            if row is not None
            else []
        )
        return list_of_maps

    def get_indexes(self, connection, table_name, schema=None, **kw):
        if schema is None or "" == schema.strip():
            schema = RadioDuckDialect.default_schema_name

        rows = self._execute_query(
            connection, get_indexes, schema, table_name
        )  # list of list
        list_of_maps = [
            {"name": row[0], "sql": row[1], "unique": row[2]} for row in rows
        ]
        for mp in list_of_maps:
            # add column names
            mp["column_names"] = []
            # parse sql for column names
            sql = mp["sql"]
            match = re.search(r"\((.*?)\)", sql)
            if match:
                columns = match.group(1).split(",")
                columns = [column.strip() for column in columns]
                mp["column_names"] = columns
            del mp["sql"]

        return list_of_maps

    def get_foreign_keys(self, connection, table_name, schema=None, **kw):
        if schema is None or "" == schema.strip():
            schema = RadioDuckDialect.default_schema_name

        rows = self._execute_query(
            connection, get_constraints, schema, table_name, "FOREIGN KEY"
        )  # list of list
        list_of_maps = [
            {"name": row[0], "column_names": row[1]} for row in rows
        ]
        return list_of_maps

    def get_columns(self, connection, table_name, schema=None, **kw):
        if schema is None or "" == schema.strip():
            schema = RadioDuckDialect.default_schema_name

        # query = f"SET schema '{schema}'; PRAGMA table_info('{table_name}')"
        query = get_columns.format(schema, table_name)
        rows = self._execute_query(connection, query)  # list of list
        list_of_maps = [
            {
                "name": row[1],
                "type": db_types.get_alchemy_type(row[2]),
                "nullable": not row[3],  # outputcolumn is 'notnull'
                "default": row[4],
                # "autoincrement": "",
                "primary_key": row[5],
            }
            for row in rows
        ]
        # not sending 'autoincrement' & 'sequence'
        # duckdb does not have these, hence not in result
        return list_of_maps

    def get_check_constraints(
        self, connection, table_name, schema=None, **kw
    ) -> list[dict[str, Any]]:
        if schema is None or "" == schema.strip():
            schema = RadioDuckDialect.default_schema_name

        rows = self._execute_query(
            connection, get_constraints, schema, table_name, "CHECK"
        )  # list of list
        list_of_maps = [{"name": row[0], "sqltext": row[1]} for row in rows]
        # not including keys 'autoincrement' & 'sequence' -
        # duckdb does not have these, hence not in result
        return list_of_maps

    def get_isolation_level(self, dbapi_conn) -> str | None:
        return self.isolation_level

    def get_default_isolation_level(self, dbapi_conn):
        # we have only snapshot
        return self.isolation_level

    def get_schema_names(
        self, connection: sqlalchemy.engine.base.Connection, **kw
    ):
        """
        superset ui asks the dialect to list schemas too
        this is not part of alchemy specification
        :param connection: alchemy base connection
        :param kw:
        :return list of schema names where
        catalog_name is neither temp not system:
        """
        rows = self._execute_query(connection, get_schemas)
        return [val for row in rows for val in row]

    def _execute_query(
        self,
        connection: sqlalchemy.engine.base.Connection,
        query: str,
        *params,
        **kw,
    ):
        if not params:
            result = connection.execute(query)
        else:
            result = connection.execute(
                query, params
            )  # use qmark ? style for params
        return result.fetchall()  # list of list
