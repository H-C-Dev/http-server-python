import pytest
from hango.server import HTTPServer, Server
from hango.http import CustomResponse
from hango.core import ContentType

@pytest.fixture
def server():
    return Server("0.0.0.0", 8080)

@pytest.fixture
def http_server():
    return HTTPServer("0.0.0.0", 8080)

@pytest.fixture


def test_invoke_handler(server):
    mock_value = "testing..."

    def mock_handler(text):
        return CustomResponse(body=text, status_code="200")
    expected_response = CustomResponse(body=mock_value, status_code="200")
    actual_response = server._Server_invoke_handler(mock_handler, mock_value)

    assert actual_response.body == expected_response.body
    assert actual_response.status_code == expected_response.status_code
    assert actual_response.content_type == expected_response.content_type
    assert actual_response.body == expected_response.body
    assert actual_response.status_line == expected_response.status_line
    assert actual_response.header_block == expected_response.header_block


def test__extract_raw_path_and_method(server):
    method = "POST"
    path = "/test"
    mock_request = {"method": method, "path": path}

    (actual_method, actual_path) = server._Server__extract_raw_path_and_method(mock_request)
    expected_method = method
    expected_path = path

    assert actual_method == expected_method
    assert actual_path == expected_path


def test_handle_request(mocker, server):
    mock_request = {
        "method" : "GET",
        "path" : "/test",
        "version" : "HTTP/1.1",
        "query" : {},
        "body" : b"",
        "headers" : {}
        }
    
    mocker.patch.object(server, "_Server__extract_raw_path_and_method", return_value=("GET", "/test"))
    expected = CustomResponse(b"testing", "200", ContentType.PLAIN.value)
    mocker.patch.object(server, "_Server__handle_GET_request", return_value=expected)

    actual = server.handle_request(mock_request)
    assert isinstance(actual, CustomResponse)
    assert actual.status_code == expected.status_code
    assert actual.content_type == expected.content_type
    assert actual.body == expected.body
    # __hanndle_POST_request
    # raise MethodNotAllowed

def test__enter_accept_state_one_iteration(mocker, http_server):
    mock_socket = mocker.Mock()
    mock_client_socket = mocker.Mock()
    mock_client_address = ("127.0.0.1", 65535)


    # [Learning]: use side_effect to manipulate the accept_connection behaviour
    mock_socket.accept_connection.side_effect = [
        (mock_client_socket, mock_client_address),
        # pretend to raise a Exception from accept_connection to terminate the accept state loop
        Exception("Terminate accept state loop")
    ]

    # [Learning]: First arg: class, Second arg: method name in str form, Third arg: simulate expected val
    mocker.patch.object(http_server, "parse_request", return_value={"method": "GET", "path": "/"})

    # mock the CustomResponse for the sake of isolation
    mock_response = mocker.Mock(spec=CustomResponse)
    mock_response.construct_response.return_value = b"testing"
    mocker.patch.object(http_server, "handle_request", return_value=mock_response)

    # [Learning]: use pytest.raises to raise the Exception to break out of infinite loop.
    with pytest.raises(Exception, match="Terminate accept state loop"):
        http_server._HTTPServer__enter_accept_state(mock_socket)

    # [Learning]: assert_called -> make sure the method has been called
    mock_socket.accept_connection.assert_called()
    # [Learning]: assert_called_with -> it called the method with the byte: "testing"
    mock_client_socket.sendall.assert_called_with(b"testing")
    mock_client_socket.close.assert_called()