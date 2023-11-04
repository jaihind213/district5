import time

import pytest

from radio_duck import InterfaceError, OperationalError, connect

http_server_port = 9001


def test_bad_scheme():
    try:
        connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="grpc",
        )
        pytest.fail(
            "Gave wrong scheme but connection created successfully & did not throw error. failing test"  # noqa: E501,B950
        )
    except InterfaceError as e:
        assert "driver only supports http scheme" in e.msg.lower()


def test_bad_url():
    try:
        connect(
            host="mandolorian_rocks",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
        )
        pytest.fail(
            "Gave wrong host,port but connection created successfully ! failing test"  # noqa: E501,B950
        )
    except Exception as expected:  # noqa: F841
        pass


def test_connection_open_close():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        return "{}"

    with app.run("localhost", http_server_port):
        conn = connect(
            host="localhost",
            port=http_server_port,
            api="/bad_enpoint",
            scheme="http",
        )
        with conn.cursor() as cursor:
            try:
                cursor.execute("select * from pond")
                pytest.fail(
                    "Gave wrong endpoint, expected error. failing test"
                )  # noqa: E501
            except Exception as e:
                # if we get 404,
                # => connection was opened successfully.
                # 404 is valid response.
                assert "404" in e.msg
        conn.close()
        try:
            conn.cursor()
            pytest.fail("Created cursor on closed connection. failing test")
        except Exception as expected:  # noqa: F841
            pass


def test_connection_timeout():
    from http_server_mock import HttpServerMock

    app = HttpServerMock(__name__)

    timeout_sec = 3

    @app.route("/v1/sql/", methods=["POST"])
    def index():
        time.sleep(timeout_sec + 2)
        return "{}"

    with app.run("localhost", http_server_port):
        with connect(
            host="localhost",
            port=http_server_port,
            api="/v1/sql/",
            scheme="http",
            timeout_sec=timeout_sec,
        ) as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute("select * from pond")
                    pytest.fail("should timeout but did not. failing test")
                except OperationalError as e:
                    assert "timed out" in str(e)
