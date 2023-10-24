import unittest

import flask

import radio_duck
from radio_duck import OperationalError
from radio_duck.sqlalchemy import RadioDuckDialect

http_server_port = 9000


def test_get_driver_name():
    dialect = RadioDuckDialect()
    assert dialect.name == "radio_duck"
    assert dialect.driver == "district5"


def test_get_isolation():
    dialect = RadioDuckDialect()
    assert dialect.isolation_level == "SNAPSHOT"
    assert dialect.get_isolation_level(None) == "SNAPSHOT"


def test_connect():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        return (
            """ {
    "schema": [
        "NUMBER"
    ],
    "columns": [
        "count_star"
    ],
    "rows": [[5]] }""",
            200,
        )

    dialect = RadioDuckDialect(dbapi=radio_duck)
    with app.run("localhost", http_server_port):
        with dialect.connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute("select count(*) as count_star from pond")
                row = cursor.fetchone()
                assert 5 == row[0]


def test_ping():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        return "response_for_ping", 400

    with app.run("localhost", http_server_port):
        dialect = RadioDuckDialect(dbapi=radio_duck)
        with dialect.connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            dialect.do_ping(conn)


def test_is_disconnect():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        return "{}", 200

    dialect = RadioDuckDialect(dbapi=radio_duck)
    assert not dialect.is_disconnect(None, None, None)
    assert not dialect.is_disconnect(OperationalError(msg="hi"), None, None)
    assert dialect.is_disconnect(
        OperationalError(msg=radio_duck.db.connect_close_resource_msg),
        None,
        None,
    )


def test_has_index():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        json = flask.request.json
        request_idx_name = json["parameters"][2]
        response_rows = (
            '"rows":[["title_idx"]]'
            if request_idx_name == "title_idx"
            else '"rows":[]'
        )
        resp = f"""{{
          "schema": [
            "STRING"
          ],
          "columns": [
            "indexname"
          ],
          {response_rows}
        }}"""
        print(resp)
        resp = resp.replace("\n", " ")
        return resp

    with app.run("localhost", http_server_port):
        dialect = RadioDuckDialect(dbapi=radio_duck)
        with dialect.connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            assert dialect.has_index(conn, "films", "title_idx", "main")
            assert not dialect.has_index(conn, "films", "unknown_idx", "main")


def test_has_table():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        json = flask.request.json
        request_table_name = json["parameters"][1]
        response_rows = (
            '"rows":[["pond"]]'
            if request_table_name == "pond"
            else '"rows":[]'
        )
        resp = f"""{{
          "schema": [
            "string"
          ],
          "columns": [
            "table_name"
          ],
          {response_rows}
        }}"""
        print(resp)
        resp = resp.replace("\n", " ")
        return resp

    with app.run("localhost", http_server_port):
        dialect = RadioDuckDialect(dbapi=radio_duck)
        with dialect.connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            assert dialect.has_table(conn, "pond", "main")
            assert not dialect.has_table(conn, "foobar", "main")


def test_has_seq():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        json = flask.request.json
        request_table_name = json["parameters"][1]
        response_rows = (
            '"rows":[["serial"]]'
            if request_table_name == "serial"
            else '"rows":[]'
        )
        resp = f"""{{
          "schema": [
            "string"
          ],
          "columns": [
            "sequencename"
          ],
          {response_rows}
        }}"""
        print(resp)
        resp = resp.replace("\n", " ")
        return resp

    with app.run("localhost", http_server_port):
        dialect = RadioDuckDialect(dbapi=radio_duck)
        with dialect.connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            assert dialect.has_sequence(conn, "serial", "main")
            assert not dialect.has_sequence(conn, "foobar", "main")


def test_get_tables():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        json = flask.request.json
        request_schema_name = json["parameters"][0]
        response_rows = (
            '"rows":[["pond"]]'
            if request_schema_name == "main"
            else '"rows":[]'
        )
        resp = f"""{{
          "schema": [
            "string"
          ],
          "columns": [
            "tablename"
          ],
          {response_rows}
        }}"""
        print(resp)
        resp = resp.replace("\n", " ")
        return resp

    with app.run("localhost", http_server_port):
        dialect = RadioDuckDialect(dbapi=radio_duck)
        with dialect.connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            assert ["pond"] == dialect.get_table_names(conn)
            assert [] == dialect.get_table_names(conn, "foobar")


def test_get_views():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        json = flask.request.json
        request_schema_name = json["parameters"][0]
        response_rows = (
            '"rows":[["pond_view"]]'
            if request_schema_name == "main"
            else '"rows":[]'
        )
        resp = f"""{{
          "schema": [
            "string"
          ],
          "columns": [
            "view_name"
          ],
          {response_rows}
        }}"""
        print(resp)
        resp = resp.replace("\n", " ")
        return resp

    with app.run("localhost", http_server_port):
        dialect = RadioDuckDialect(dbapi=radio_duck)
        with dialect.connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            assert ["pond_view"] == dialect.get_view_names(conn)
            assert [] == dialect.get_view_names(conn, "foobar")


def test_get_view_sql():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        json = flask.request.json
        request_view_name = json["parameters"][1]
        response_rows = (
            '"rows":[["CREATE VIEW pond_view AS SELECT * FROM pond"]]'
            if request_view_name == "pond_view"
            else '"rows":[]'
        )
        resp = f"""{{
          "schema": [
            "string"
          ],
          "columns": [
            "sql"
          ],
          {response_rows}
        }}"""
        print(resp)
        resp = resp.replace("\n", " ")
        return resp

    with app.run("localhost", http_server_port):
        dialect = RadioDuckDialect(dbapi=radio_duck)
        with dialect.connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            expected = "CREATE VIEW pond_view AS SELECT * FROM pond"
            actual = dialect.get_view_definition(conn, "pond_view")
            assert expected == actual
            assert "" == dialect.get_view_definition(conn, "foobar")


def test_get_uniq_constraints():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        json = flask.request.json
        table_name = json["parameters"][1]
        response_rows = (
            '"rows":[ ["UNIQUE(id, id)", ["id"] ] ]'
            if table_name == "students"
            else '"rows":[]'
        )
        resp = f"""{{
          "schema": [
            "string","list"
          ],
          "columns": [
            "name", "column_names"
          ],
          {response_rows}
        }}"""
        print(resp)
        resp = resp.replace("\n", " ")
        return resp

    with app.run("localhost", http_server_port):
        dialect = RadioDuckDialect(dbapi=radio_duck)
        with dialect.connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            assert [
                {"name": "UNIQUE(id, id)", "column_names": ["id"]}
            ] == dialect.get_unique_constraints(conn, "students")
            assert [] == dialect.get_unique_constraints(conn, "foobar")


def test_get_temp_views():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        response_rows = '"rows":[["temp_view"]]'
        resp = f"""{{
          "schema": [
            "string"
          ],
          "columns": [
            "view_name"
          ],
          {response_rows}
        }}"""
        print(resp)
        resp = resp.replace("\n", " ")
        return resp

    with app.run("localhost", http_server_port):
        dialect = RadioDuckDialect(dbapi=radio_duck)
        with dialect.connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            assert ["temp_view"] == dialect.get_temp_view_names(conn, "main")
            assert ["temp_view"] == dialect.get_temp_view_names(conn, "foobar")
            assert ["temp_view"] == dialect.get_temp_view_names(conn)


def test_get_temp_tables():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        json = flask.request.json
        schema_name = json["parameters"][0]
        response_rows = (
            '"rows":[ ["temp_table"] ]'
            if schema_name == "main"
            else '"rows":[]'
        )
        resp = f"""{{
          "schema": [
            "string"
          ],
          "columns": [
            "table_name"
          ],
          {response_rows}
        }}"""
        print(resp)
        resp = resp.replace("\n", " ")
        return resp

    with app.run("localhost", http_server_port):
        dialect = RadioDuckDialect(dbapi=radio_duck)
        with dialect.connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            assert ["temp_table"] == dialect.get_temp_table_names(conn)
            assert [] == dialect.get_temp_table_names(conn, "foobar")


def test_get_seqs():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        json = flask.request.json
        schema_name = json["parameters"][0]
        response_rows = (
            '"rows":[ ["seq1"] ]' if schema_name == "main" else '"rows":[]'
        )
        resp = f"""{{
          "schema": [
            "string"
          ],
          "columns": [
            "sequencename"
          ],
          {response_rows}
        }}"""
        print(resp)
        resp = resp.replace("\n", " ")
        return resp

    with app.run("localhost", http_server_port):
        dialect = RadioDuckDialect(dbapi=radio_duck)
        with dialect.connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            assert ["seq1"] == dialect.get_sequence_names(conn)
            assert [] == dialect.get_sequence_names(conn, "foobar")


def test_get_pk():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        json = flask.request.json
        table_name = json["parameters"][1]
        response_rows = (
            '"rows":[ ["PRIMARY KEY(id)", ["id"] ] ]'
            if table_name == "students"
            else '"rows":[]'
        )
        resp = f"""{{
          "schema": [
            "string","list"
          ],
          "columns": [
            "name", "column_names"
          ],
          {response_rows}
        }}"""
        print(resp)
        resp = resp.replace("\n", " ")
        return resp

    with app.run("localhost", http_server_port):
        dialect = RadioDuckDialect(dbapi=radio_duck)
        with dialect.connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            assert [
                {"name": "PRIMARY KEY(id)", "column_names": ["id"]}
            ] == dialect.get_pk_constraint(conn, "students")
            assert [] == dialect.get_pk_constraint(conn, "foobar")


def test_get_indexes():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        json = flask.request.json
        table_name = json["parameters"][1]
        response_rows = (
            '"rows":[ ["city_id_ndex", "CREATE INDEX city_id_ndex ON employee (city,id);", false] ]'  # noqa: E501,B950
            if table_name == "employee"
            else '"rows":[]'
        )
        resp = f"""{{
          "schema": [
            "string","string","bool"
          ],
          "columns": [
            "index_name","sql","is_unique"
          ],
          {response_rows}
        }}"""
        print(resp)
        resp = resp.replace("\n", " ")
        return resp

    with app.run("localhost", http_server_port):
        dialect = RadioDuckDialect(dbapi=radio_duck)
        with dialect.connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            assert [
                {
                    "name": "city_id_ndex",
                    "column_names": ["city", "id"],
                    "unique": False,
                }
            ] == dialect.get_indexes(conn, "employee")
            assert [] == dialect.get_indexes(conn, "foobar")


def test_get_fk():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        json = flask.request.json
        table_name = json["parameters"][1]
        response_rows = (
            '"rows":[ ["FOREIGN KEY (t1_id) REFERENCES t1(id)", ["t1_id"] ] ]'
            if table_name == "t2"
            else '"rows":[]'
        )
        resp = f"""{{
          "schema": [
            "string","list"
          ],
          "columns": [
            "name", "column_names"
          ],
          {response_rows}
        }}"""
        print(resp)
        resp = resp.replace("\n", " ")
        return resp

    with app.run("localhost", http_server_port):
        dialect = RadioDuckDialect(dbapi=radio_duck)
        with dialect.connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            assert [
                {
                    "name": "FOREIGN KEY (t1_id) REFERENCES t1(id)",
                    "column_names": ["t1_id"],
                }
            ] == dialect.get_foreign_keys(conn, "t2")
            assert [] == dialect.get_pk_constraint(conn, "foobar")


def test_get_columns():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        json = flask.request.json
        table_name = json["parameters"][1]
        response_rows = (
            '"rows":[ ["id", "INTEGER",false, "1" ] ]'
            if table_name == "t2"
            else '"rows":[]'
        )
        resp = f"""{{
          "schema": [
            "string","string", "bool", "string"
          ],
          "columns": [
            "name", "type", "nullable", "default"
          ],
          {response_rows}
        }}"""
        print(resp)
        resp = resp.replace("\n", " ")
        return resp

    with app.run("localhost", http_server_port):
        dialect = RadioDuckDialect(dbapi=radio_duck)
        with dialect.connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            assert [
                {
                    "name": "id",
                    "type": "INTEGER",
                    "nullable": False,
                    "default": "1",
                }
            ] == dialect.get_columns(conn, "t2")
            assert [] == dialect.get_pk_constraint(conn, "foobar")


def test_get_checks():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        json = flask.request.json
        table_name = json["parameters"][1]
        response_rows = (
            '"rows":[ ["CHECK((x<y))" , "(x<y)" ] ]'
            if table_name == "t2"
            else '"rows":[]'
        )
        resp = f"""{{
          "schema": [
            "string","string"
          ],
          "columns": [
            "name", "sqltext"
          ],
          {response_rows}
        }}"""
        print(resp)
        resp = resp.replace("\n", " ")
        return resp

    with app.run("localhost", http_server_port):
        dialect = RadioDuckDialect(dbapi=radio_duck)
        with dialect.connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            assert [
                {"name": "CHECK((x<y))", "sqltext": "(x<y)"}
            ] == dialect.get_check_constraints(conn, "t2")
            assert [] == dialect.get_check_constraints(conn, "foobar")


class NotImplementedTest(unittest.TestCase):
    def test_get_table_comment(self):
        dialect = RadioDuckDialect(dbapi=radio_duck)
        with self.assertRaises(NotImplementedError):
            dialect.get_table_comment(None, None)
