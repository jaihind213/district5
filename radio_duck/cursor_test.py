import pytest

from radio_duck import OperationalError, ProgrammingError, connect, db_types
from radio_duck.connection_test import http_server_port


def test_no_query():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        return "{}"

    with app.run("localhost", http_server_port):
        try:
            with connect(
                host="localhost",
                port=http_server_port,
                api="/v1/sql/",
                scheme="http",  # noqa: E501
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("   ")
                    pytest.fail(
                        "Gave empty query but did not error out. failing test"
                    )  # noqa: E501
        except ProgrammingError as e:
            assert "query is empty" in e.msg.lower()


def test_cursor_description():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        return (
            """{
              "schema": [
                "STRING", "NUMBER"
              ],
              "columns": [
                "duck_type", "total"
              ],
              "rows": [["mallard", 1], ["marbled_duck", 2]]
            }
        """,
            200,
        )

    with app.run("localhost", http_server_port):
        conn = connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        )
        cursor = conn.cursor()
        cursor.execute("select duck_type from pond")
        cursor_desc = cursor.description

        assert 2 == len(
            cursor_desc
        ), "expecting 2 descrirption for 2 column selected"  # noqa: E501
        for string_col_desc in cursor_desc:
            assert 7 == len(
                string_col_desc
            ), "expecting sequence of size 7 for each description"
        string_col_desc = cursor_desc[0]
        assert (
            string_col_desc[0] == "duck_type"
        ), "expected col name in cursor description to be 'duck_type'"
        assert string_col_desc[1] == db_types.get_type_code(
            "STRING"
        ), "expected col type in cursor description to be 'STRING'"

        num_col_desc = cursor_desc[1]
        assert (
            num_col_desc[0] == "total"
        ), "expected col name in cursor description to be 'total'"
        assert num_col_desc[1] == db_types.get_type_code(
            "NUMBER"
        ), "expected col type in cursor description to be 'NUMBER'"


def test_cursor_iteration():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        return (
            """{
              "schema": [
                "STRING"
              ],
              "columns": [
                "some_number"
              ],
              "rows": [["one"], ["two"], ["three"],
              ["four"], ["five"], ["six"]]
            }
        """,
            200,
        )

    with app.run("localhost", http_server_port):
        with connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            with conn.cursor() as cursor:
                assert (
                    -1 == cursor.rowcount
                ), "testing rowcount before execution"  # noqa: E501
                cursor.execute("select some_number from numbers")
                assert 6 == cursor.rowcount, "testing rowcount after execution"
                # set & test fetch size
                cursor.arraysize = 2
                assert 2 == cursor.arraysize

                row = cursor.fetchone()
                assert row is not None
                assert "one" == row[0]

                twoRows = cursor.fetchmany()
                assert twoRows is not None
                assert cursor.arraysize == len(twoRows)
                assert "two" == twoRows[0][0]
                assert "three" == twoRows[1][0]

                remaining = cursor.fetchall()
                assert remaining is not None
                assert len(remaining) == 3
                assert "four" == remaining[0][0]
                assert "five" == remaining[1][0]
                assert "six" == remaining[2][0]

                # no more left
                assert cursor.fetchone() is None
                anymore = [cursor.fetchall(), cursor.fetchmany(2)]
                for am in anymore:
                    assert am is not None
                    assert 0 == len(am)


def test_cursor_close():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        return (
            """{
              "schema": [
                "STRING"
              ],
              "columns": [
                "some_number"
              ],
              "rows": [["one"]]
            }
        """,
            200,
        )

    with app.run("localhost", http_server_port):
        with connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("select some_number from numbers")
            finally:
                cursor.close()
                try:
                    cursor.execute("select total from bank")
                except Exception as e:
                    assert "already closed" in e.msg
                try:
                    cursor.fetchone()
                except Exception as e:
                    assert "already closed" in e.msg
                try:
                    cursor.fetchall()
                except Exception as e:
                    assert "already closed" in e.msg
                try:
                    cursor.fetchmany(2)
                except Exception as e:
                    assert "already closed" in e.msg


def test_for_non200response():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        raise Exception("internal error")

    @app.route("/v2/sql/", methods=["POST"])
    def index1():
        return "{}", 408

    with app.run("localhost", http_server_port):
        with connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute("select * from pond")
                    pytest.fail(
                        "api endpoint throws 500 but cursor.execute() did not error out . failing test"  # noqa: E501,B950
                    )
                except Exception as e:
                    assert isinstance(e, OperationalError)
                    assert (
                        "failed to execute query. response status: 500"
                        in e.msg
                    )  # noqa: E501
        with connect(
            host="localhost",
            port=http_server_port,
            api="/v2/sql/",
            scheme="http",
        ) as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute("select * from")
                    pytest.fail(
                        "api endpoint throws 400, but cursor.execute() did not error out . failing test"  # noqa: E501,B950
                    )
                except Exception as e:
                    assert isinstance(e, ProgrammingError)
                    assert (
                        "failed to execute query. response status: 408"
                        in e.msg
                    )  # noqa: E501


def test_for_bad_response_json():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        return "this is not a json!", 200

    with app.run("localhost", http_server_port):
        with connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute("select * from pond")
                    pytest.fail(
                        "api returned bad json,"
                        " but cursor.execute() did not error out. failing test"
                    )
                except Exception as e:
                    assert isinstance(e, OperationalError)
                    assert "could not deserialize response" in e.msg


def test_fetch_before_execute():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        return "{}", 200

    with app.run("localhost", http_server_port):
        with connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        ) as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.fetchone()
                except Exception as e:
                    assert isinstance(e, ProgrammingError)
                try:
                    cursor.fetchall()
                except Exception as e:
                    assert isinstance(e, ProgrammingError)
                try:
                    cursor.fetchmany()
                except Exception as e:
                    assert isinstance(e, ProgrammingError)


@pytest.mark.integration_test
def test_with_server():
    # start radio-duck server for this test
    # https://github.com/jaihind213/radio-duck
    with connect(
        host="localhost", port=8000, api="/v1/sql/", scheme="http"
    ) as conn:
        with conn.cursor() as cursor:
            # good query1
            cursor.execute(
                "select total from pond where duck_type = ? ", ["mighty_duck"]
            )
            assert cursor.rowcount > 0, "testing rowcount after execution"
            row = cursor.fetchone()
            assert row is not None
            assert row[0] > 1

            # reuse cursor
            try:
                # bad query1 where ? is missing but parameters given
                cursor.execute(
                    "select total from pond where duck_type", ["mighty_duck"]
                )
            except Exception as e:
                assert "Invalid Input Error" in e.msg
                assert isinstance(e, ProgrammingError)
            try:
                # bad query2
                cursor.execute("select column from ")
            except Exception as e:
                assert "Parser Error" in e.msg
                assert isinstance(e, ProgrammingError)

            # good query again after bad queries
            cursor.execute(
                "select total from pond where duck_type = ? ", ["a_whale"]
            )  # noqa: E501
            assert cursor.rowcount == 0, "testing rowcount after execution"
            row = cursor.fetchone()
            assert row is None
