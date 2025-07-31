import pytest
from hango.server import HTTPServer, Server
from unittest.mock import AsyncMock, MagicMock, Mock
from hango.core import ContentType, ServiceContainer
import asyncio


@pytest.fixture
def mock_container():
    return MagicMock()


@pytest.fixture
def server():
    return Server("0.0.0.0", 8080, mock_container)

@pytest.fixture
def http_server():
    return HTTPServer("0.0.0.0", 8080, ServiceContainer())

@pytest.fixture
def mock_reader():
    return MagicMock()

@pytest.fixture
def mock_writer():
    return MagicMock()

@pytest.fixture
def mock_request():
    return MagicMock()

@pytest.fixture
def mock_connection_manager():
    return MagicMock()

@pytest.fixture
def mock_connection_id():
    return "123"

@pytest.fixture
def mock_response():
    return MagicMock()

@pytest.mark.asyncio
async def test__handle_client(monkeypatch, http_server, mock_reader, mock_writer, mock_request, mock_connection_manager, mock_connection_id):
    spy_clean_up_connection = AsyncMock()
    monkeypatch.setattr(http_server, "_register_connection_manager", AsyncMock(return_value=("123", mock_connection_manager)))
    monkeypatch.setattr(http_server, "_process_request", AsyncMock(return_value=mock_request))
    monkeypatch.setattr(http_server, "_clean_up_connection", spy_clean_up_connection)
    await http_server._handle_client(mock_reader, mock_writer)
    http_server._process_request.assert_awaited_once_with(mock_reader, mock_writer)
    http_server._clean_up_connection.assert_awaited_once_with(mock_connection_id, mock_connection_manager, mock_request, mock_writer)
    spy_clean_up_connection.assert_awaited_once_with(mock_connection_id, mock_connection_manager, mock_request, mock_writer)
    assert http_server._clean_up_connection is spy_clean_up_connection

@pytest.mark.asyncio
@pytest.mark.parametrize("connection, should_close", [("close", True), ("keep-alive", False)])
async def test__clean_up_connection(monkeypatch, http_server, mock_writer, mock_request, mock_connection_manager, mock_connection_id, connection, should_close):
    spy_deregister = AsyncMock()
    spy_close_connection = AsyncMock()
    monkeypatch.setattr(mock_connection_manager, "deregister", spy_deregister)
    mock_request.headers.connection = connection
    monkeypatch.setattr(http_server, "_close_connection", spy_close_connection)
    await http_server._clean_up_connection(mock_connection_id, mock_connection_manager, mock_request, mock_writer)

    mock_connection_manager.deregister.assert_awaited_once_with(mock_connection_id)
    if should_close:
        http_server._close_connection.assert_awaited_once_with(mock_writer)
        assert http_server._close_connection is spy_close_connection
    else:
        http_server._close_connection.assert_not_awaited()
        assert http_server._close_connection is spy_close_connection
        
@pytest.mark.asyncio
async def test__process_request(monkeypatch, server):
    mock_handler = MagicMock()
    mock_is_static_prefix = False
    mock_local_middlewares = []

    monkeypatch.setattr(server, "parse_request", AsyncMock(return_value=(mock_request, mock_handler, mock_is_static_prefix, mock_local_middlewares)))
    monkeypatch.setattr(server, "handle_request", AsyncMock(return_value=mock_response))
    spy_server_respond = AsyncMock()
    monkeypatch.setattr(server, "server_respond", spy_server_respond)
    await server._process_request(mock_reader, mock_writer)

    server.parse_request.assert_awaited_once_with(mock_reader, mock_writer)
    server.handle_request.assert_awaited_once_with(mock_request, mock_handler, mock_writer, mock_is_static_prefix, mock_local_middlewares)
    server.server_respond.assert_awaited_once_with(mock_response, mock_writer)

@pytest.fixture
def mock_raw_response():
    return b"HTTP/1.1 200 OK\r\n\r\nHello"


@pytest.mark.asyncio
async def test_server_respond(http_server):
    http_server._send_response = AsyncMock()
    http_server._close_connection = AsyncMock()
    # writer = MagicMock()
    mock_writer.drain = AsyncMock()
    mock_writer.wait_closed = AsyncMock()
    is_early_hints = False
    await http_server.server_respond(mock_raw_response, mock_writer, is_early_hints)
    http_server._send_response.assert_awaited_once_with(mock_raw_response, mock_writer)
    http_server._close_connection.assert_awaited_once_with(mock_writer, is_early_hints)

@pytest.mark.asyncio
async def test__send_response(http_server):
    mock_writer = MagicMock()
    mock_writer.drain = AsyncMock()
    await http_server._send_response(mock_raw_response, mock_writer)
    mock_writer.write.assert_called_once_with(mock_raw_response)
    mock_writer.drain.assert_awaited_once()

@pytest.mark.asyncio
async def test__close_connection(http_server):
    mock_writer = MagicMock()
    mock_writer.wait_closed = AsyncMock()
    await http_server._close_connection(mock_writer, False)
    mock_writer.wait_closed.assert_awaited_once()



@pytest.mark.asyncio
async def test_init_server(monkeypatch, http_server):
    
    spy_mock_server = AsyncMock(return_value=http_server)
    monkeypatch.setattr(asyncio, "start_server", spy_mock_server)
    result = await http_server.init_server()
    spy_mock_server.assert_awaited_once_with(
        client_connected_cb=http_server._handle_client,
        host=http_server.host,
        port=http_server.port
    )
    assert result is http_server
    

def test_handle_error_response_functional(http_server):
    dummy_error = type("DummyError", (), {"message": "something went wrong", "status_code": 400})()
    encoded = http_server.handle_error_response(dummy_error)
    text = encoded.decode()
    assert text.startswith(f"HTTP/1.1 {dummy_error.status_code}")
    assert dummy_error.message in text
    assert f"Content-Type: {ContentType.PLAIN.value}" in text

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

@pytest.mark.parametrize("mock_concurrency_model", ['process', 'thread', ''])
def test__load_concurrency_model(server, mock_concurrency_model):
    server.concurrency_model = mock_concurrency_model

    server._load_concurrency_model()
    if mock_concurrency_model == 'process':
        assert isinstance(server._executor, ProcessPoolExecutor)
    elif mock_concurrency_model == 'thread':
        assert isinstance(server._executor, ThreadPoolExecutor)
    else: 
        assert server._executor is None


def test_set_global_middlewares(server, mock_container):
    mock_chain = MagicMock()
    mock_container.get.return_value = mock_chain
    server = Server("0.0.0.0", 8080, mock_container)

    def mock_middleware(request):
        return request
    
    returned = server.set_global_middlewares(mock_middleware)

    mock_chain.add_middleware.assert_called_once_with(mock_middleware)
    assert returned is mock_middleware


def test_set_hook_before_each_handler(server, mock_container):
    mock_chain = MagicMock()
    mock_container.get.return_value = mock_chain
    server = Server("0.0.0.0", 8080, mock_container)

    def mock_hoook(request):
        return request
    
    returned = server.set_hook_before_each_handler(mock_chain)

    mock_chain.add_hook_before_each_handler(mock_hoook)
    assert returned is mock_chain

def test_set_hook_after_each_handler(server, mock_container):
    mock_chain = MagicMock()
    mock_container.get.return_value = mock_chain
    server = Server("0.0.0.0", 8080, mock_container)

    def mock_hoook(request):
        return request
    
    returned = server.set_hook_after_each_handler(mock_chain)

    mock_chain.add_hook_after_each_handler(mock_hoook)
    assert returned is mock_chain

    



# def test_invoke_handler(server):
#     mock_value = "testing..."

#     def mock_handler(text):
#         return CustomResponse(body=text, status_code="200")
#     expected_response = CustomResponse(body=mock_value, status_code="200")
#     actual_response = server._Server_invoke_handler(mock_handler, mock_value)

#     assert actual_response.body == expected_response.body
#     assert actual_response.status_code == expected_response.status_code
#     assert actual_response.content_type == expected_response.content_type
#     assert actual_response.body == expected_response.body
#     assert actual_response.status_line == expected_response.status_line
#     assert actual_response.header_block == expected_response.header_block


# def test__extract_raw_path_and_method(server):
#     method = "POST"
#     path = "/test"
#     mock_request = {"method": method, "path": path}

#     (actual_method, actual_path) = server._Server__extract_raw_path_and_method(mock_request)
#     expected_method = method
#     expected_path = path

#     assert actual_method == expected_method
#     assert actual_path == expected_path


# def test_handle_request(mocker, server):
#     mock_request = {
#         "method" : "GET",
#         "path" : "/test",
#         "version" : "HTTP/1.1",
#         "query" : {},
#         "body" : b"",
#         "headers" : {}
#         }
    
#     mocker.patch.object(server, "_Server__extract_raw_path_and_method", return_value=("GET", "/test"))
#     expected = CustomResponse(b"testing", "200", ContentType.PLAIN.value)
#     mocker.patch.object(server, "_Server__handle_GET_request", return_value=expected)

#     actual = server.handle_request(mock_request)
#     assert isinstance(actual, CustomResponse)
#     assert actual.status_code == expected.status_code
#     assert actual.content_type == expected.content_type
#     assert actual.body == expected.body
#     # __hanndle_POST_request
#     # raise MethodNotAllowed

# def test__enter_accept_state_one_iteration(mocker, http_server):
#     mock_socket = mocker.Mock()
#     mock_client_socket = mocker.Mock()
#     mock_client_address = ("127.0.0.1", 65535)


#     # [Learning]: use side_effect to manipulate the accept_connection behaviour
#     mock_socket.accept_connection.side_effect = [
#         (mock_client_socket, mock_client_address),
#         # pretend to raise a Exception from accept_connection to terminate the accept state loop
#         Exception("Terminate accept state loop")
#     ]

#     # [Learning]: First arg: class, Second arg: method name in str form, Third arg: simulate expected val
#     mocker.patch.object(http_server, "parse_request", return_value={"method": "GET", "path": "/"})

#     # mock the CustomResponse for the sake of isolation
#     mock_response = mocker.Mock(spec=CustomResponse)
#     mock_response.construct_response.return_value = b"testing"
#     mocker.patch.object(http_server, "handle_request", return_value=mock_response)

#     # [Learning]: use pytest.raises to raise the Exception to break out of infinite loop.
#     with pytest.raises(Exception, match="Terminate accept state loop"):
#         http_server._HTTPServer__enter_accept_state(mock_socket)

#     # [Learning]: assert_called -> make sure the method has been called
#     mock_socket.accept_connection.assert_called()
#     # [Learning]: assert_called_with -> it called the method with the byte: "testing"
#     mock_client_socket.sendall.assert_called_with(b"testing")
#     mock_client_socket.close.assert_called()