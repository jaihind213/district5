# from sqlalchemy.dialects import registry
# from sqlalchemy import create_engine
# dialect_name,path_to_module,className
# registry.register("radio_duck", "radio_duck.sqlalchemy", "RadioDuckDialect")


from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from radio_duck.reserved_keywords import keyword_list

if TYPE_CHECKING:
    from _typeshed import DBAPIConnection

# from _typeshed.dbapi import DBAPIConnection
from typing import Any, Callable, List

# https://docs.sqlalchemy.org/en/20/core/internals.html#sqlalchemy.engine.Dialect.do_terminate
# from sqlalchemy.engine import default, interfaces
from sqlalchemy.engine import default
from sqlalchemy.sql import compiler

import radio_duck
from radio_duck.db import connect_close_resource_msg
from radio_duck.exceptions import NotSupportedError, ProgrammingError
from radio_duck.queries import (
    get_check_constraint,
    get_columns,
    get_constraints,
    get_indexes,
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
    def do_ping(self, dbapi_connection):
        cursor = None
        incomplete_query = "select * from ;"
        try:
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute(incomplete_query)
            except ProgrammingError as expected:
                if 400 != expected.response_status:
                    raise expected
            finally:
                cursor.close()
        except self.dbapi.Error as err:
            if self.is_disconnect(err, dbapi_connection, cursor):
                return False
            else:
                raise
        else:
            return True

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
        logging.info("radio_duck dialect engine created")
        super().engine_created(engine)

    def reset_isolation_level(self, dbapi_conn) -> None:
        pass

    def set_isolation_level(self, dbapi_conn, level) -> None:
        pass

    def on_connect(self) -> Callable[[DBAPIConnection], object] | None:
        def do_on_connect(connection):
            # todo logging. set duckdb specific flags
            # connection.execute("SET SPECIAL FLAGS etc")
            logging.debug("radio_duck pre connection  establishment hook.")

        return do_on_connect

    def on_connect_url(
        self, url
    ) -> Callable[[DBAPIConnection], object] | None:
        def do_on_connect_url(connection):
            # todo logging. set duckdb specific flags
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
        cursor = None
        if schema is None or "" == schema.strip():
            schema = "main"
        try:
            cursor = connection.cursor()
            cursor.execute(
                has_index_query, parameters=[schema, table_name, index_name]
            )
            return cursor.rowcount == 1
        finally:
            if cursor is not None:
                cursor.close()

    def has_table(self, connection, table_name, schema=None, **kw) -> None:
        cursor = None
        if schema is None or "" == schema.strip():
            schema = "main"
        try:
            cursor = connection.cursor()
            cursor.execute(has_table_query, parameters=[schema, table_name])
            return cursor.rowcount == 1
        finally:
            if cursor is not None:
                cursor.close()

    def has_sequence(
        self, connection, sequence_name, schema=None, **kw
    ) -> None:
        cursor = None
        if schema is None or "" == schema.strip():
            schema = "main"
        try:
            cursor = connection.cursor()
            cursor.execute(
                has_sequence_query, parameters=[schema, sequence_name]
            )
            return cursor.rowcount == 1
        finally:
            if cursor is not None:
                cursor.close()

    # ----get methods

    def get_table_names(
        self, connection, schema=None, **kw
    ) -> List[str] | None:
        cursor = None
        if schema is None or "" == schema.strip():
            schema = "main"
        try:
            cursor = connection.cursor()
            cursor.execute(get_tables, parameters=[schema])
            rows = cursor.fetchall()  # list of list
            table_names = [col_val for row in rows for col_val in row]
            return table_names
        finally:
            if cursor is not None:
                cursor.close()

    def get_view_names(self, connection, schema=None, **kw):
        if schema is None or "" == schema.strip():
            schema = "main"
        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute(get_views, parameters=[schema])
            rows = cursor.fetchall()  # list of list
            views = [col_val for row in rows for col_val in row]
            return views
        finally:
            if cursor is not None:
                cursor.close()

    def get_view_definition(
        self, connection, view_name, schema=None, **kw
    ) -> None:
        cursor = None
        if schema is None or "" == schema.strip():
            schema = "main"
        try:
            cursor = connection.cursor()
            cursor.execute(get_view_sql, parameters=[schema, view_name])
            row = cursor.fetchone()
            return "" if row is None else row[0]  # return sql
        finally:
            if cursor is not None:
                cursor.close()

    def get_unique_constraints(
        self, connection, table_name, schema=None, **kw
    ) -> list[dict[str, Any]]:
        cursor = None
        if schema is None or "" == schema.strip():
            schema = "main"
        try:
            cursor = connection.cursor()
            cursor.execute(
                get_constraints, parameters=[schema, table_name, "UNIQUE"]
            )
            rows = cursor.fetchall()  # list of list
            list_of_maps = [
                {"name": row[0], "column_names": row[1]} for row in rows
            ]
            return list_of_maps
        finally:
            if cursor is not None:
                cursor.close()

    def get_temp_view_names(self, connection, schema=None, **kw):
        cursor = None
        try:
            cursor = connection.cursor()
            # Temporary views exist in a special schema, so a schema name
            # cannot be given when creating a temporary view.
            # The name of the view must be distinct from the name of any
            # other view or table in the same schema.
            # hence schema is ignored for query
            cursor.execute(get_temp_views, parameters=[])
            rows = cursor.fetchall()  # list of list
            temp_views = [col_val for row in rows for col_val in row]
            return temp_views
        finally:
            if cursor is not None:
                cursor.close()

    def get_temp_table_names(self, connection, schema=None, **kw):
        cursor = None
        if schema is None or "" == schema.strip():
            schema = "main"
        try:
            cursor = connection.cursor()
            cursor.execute(get_temp_tables, parameters=[schema])
            rows = cursor.fetchall()  # list of list
            temp_tables = [col_val for row in rows for col_val in row]
            return temp_tables
        finally:
            if cursor is not None:
                cursor.close()

    def get_table_comment(self, connection, table_name, schema=None, **kw):
        raise NotImplementedError()

    def get_sequence_names(self, connection, schema=None, **kw) -> list[Any]:
        cursor = None
        if schema is None or "" == schema.strip():
            schema = "main"
        try:
            cursor = connection.cursor()
            cursor.execute(get_sequences, parameters=[schema])
            rows = cursor.fetchall()  # list of list
            seq_names = [col_val for row in rows for col_val in row]
            return seq_names
        finally:
            if cursor is not None:
                cursor.close()

    def get_pk_constraint(self, connection, table_name, schema=None, **kw):
        cursor = None
        if schema is None or "" == schema.strip():
            schema = "main"
        try:
            cursor = connection.cursor()
            cursor.execute(
                get_constraints, parameters=[schema, table_name, "PRIMARY KEY"]
            )
            row = cursor.fetchone()  # list of list
            list_of_maps = (
                [{"name": row[0], "column_names": row[1]}]
                if row is not None
                else []
            )
            return list_of_maps
        finally:
            if cursor is not None:
                cursor.close()

    def get_indexes(self, connection, table_name, schema=None, **kw):
        cursor = None
        if schema is None or "" == schema.strip():
            schema = "main"
        try:
            cursor = connection.cursor()
            cursor.execute(get_indexes, parameters=[schema, table_name])
            rows = cursor.fetchall()  # list of list
            list_of_maps = [
                {"name": row[0], "sql": row[1], "unique": row[2]}
                for row in rows
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
        finally:
            if cursor is not None:
                cursor.close()

    def get_foreign_keys(self, connection, table_name, schema=None, **kw):
        cursor = None
        if schema is None or "" == schema.strip():
            schema = "main"
        try:
            cursor = connection.cursor()
            cursor.execute(
                get_constraints, parameters=[schema, table_name, "FOREIGN KEY"]
            )
            rows = cursor.fetchall()  # list of list
            list_of_maps = [
                {"name": row[0], "column_names": row[1]} for row in rows
            ]
            return list_of_maps
        finally:
            if cursor is not None:
                cursor.close()

    def get_columns(self, connection, table_name, schema=None, **kw):
        cursor = None
        if schema is None or "" == schema.strip():
            schema = "main"
        try:
            cursor = connection.cursor()
            cursor.execute(get_columns, parameters=[schema, table_name])
            rows = cursor.fetchall()  # list of list
            list_of_maps = [
                {
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2],
                    "default": row[3],
                }
                for row in rows
            ]
            # not sending 'autoincrement' & 'sequence'
            # duckdb does not have these, hence not in result
            return list_of_maps
        finally:
            if cursor is not None:
                cursor.close()

    def get_check_constraints(
        self, connection, table_name, schema=None, **kw
    ) -> None:
        cursor = None
        if schema is None or "" == schema.strip():
            schema = "main"
        try:
            cursor = connection.cursor()
            cursor.execute(
                get_check_constraint, parameters=[schema, table_name]
            )
            rows = cursor.fetchall()  # list of list
            list_of_maps = [
                {"name": row[0], "sqltext": row[1]} for row in rows
            ]
            # not including keys 'autoincrement' & 'sequence' -
            # duckdb does not have these, hence not in result
            return list_of_maps
        finally:
            if cursor is not None:
                cursor.close()

    def get_isolation_level(self, dbapi_conn) -> str | None:
        return self.isolation_level

    def get_default_isolation_level(self, dbapi_conn):
        # we have only snapshot
        return self.isolation_level
