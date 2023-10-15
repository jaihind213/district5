import time

import pytest


from radio_duck import connect, InterfaceError, OperationalError, ProgrammingError

http_server_port = 9001

def test_bad_scheme():
    try:
        connect(host="localhost", port=http_server_port, api="/v1/sql", scheme="grpc")
        pytest.fail("Gave wrong scheme but connection created successfully & did not throw error. failing test")
    except InterfaceError as e:
        assert  "driver only supports http scheme" in e.msg.lower()


def test_bad_url():
    try:
        connect(host="mandolorian_rocks", port=http_server_port, api="/v1/sql", scheme="http")
        pytest.fail("Gave wrong host,port but connection created successfully ! failing test")
    except:
        pass


def test_connection_open_close():
    from http_server_mock import HttpServerMock
    app = HttpServerMock(__name__)

    @app.route("/v1/sql", methods=["POST"])
    def index():
        return "{}"

    with app.run("localhost", http_server_port):
        conn = connect(host="localhost", port=http_server_port, api="/bad_enpoint", scheme="http")
        with conn.cursor() as cursor:
            try:
                cursor.execute("select * from pond")
            except Exception as e:
                # if we get 404, => connection was opened successfully. 404 is valid response.
                assert "404" in e.msg
        conn.close()
        try:
            conn.cursor()
            pytest.fail("Created cursor on closed connection. failing test")
        except:
            pass

def test_connection_timeout():
    from http_server_mock import HttpServerMock
    app = HttpServerMock(__name__)

    timeout_sec = 3
    @app.route("/v1/sql", methods=["POST"])
    def index():
        time.sleep(timeout_sec + 2)
        return "{}"

    with app.run("localhost", http_server_port):
        with connect(host="localhost", port=http_server_port, api="/v1/sql",
                     scheme="http", timeout_sec = timeout_sec) as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute("select * from pond")
                except OperationalError as e:
                    assert "timed out" in e.msg
