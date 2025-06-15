import pytest
from server import HTTPServer, Server
from response import CustomResponse

def test__invoke_handler():
    server = Server("0.0.0.0", 8080)
    mock_value = "testing..."

    def mock_handler(text):
        return CustomResponse(body=text, status_code=200)
    expected_response = CustomResponse(body=mock_value, status_code=200)
    actual_response = server._Server__invoke_handler(mock_handler, mock_value)

    assert actual_response.body == expected_response.body
    assert actual_response.status_code == expected_response.status_code
    assert actual_response.content_type == expected_response.content_type
    assert actual_response.body == expected_response.body
    assert actual_response.status_line == expected_response.status_line
    assert actual_response.header_block == expected_response.header_block
