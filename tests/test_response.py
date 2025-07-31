import pytest
from hango.server import HTTPServer, Server
from unittest.mock import AsyncMock, MagicMock, Mock
import asyncio
from hango.http import ResponseHeaders, Response, EarlyHintsResponse


@pytest.fixture
def mock_response_headers():
    return ResponseHeaders(status_code=200, status_message="hello", date="1/1/2020", server="0.0.0.0", content_length=0, content_type="plain")

@pytest.fixture
def mock_response():
    return Response(status_code=200)  

@pytest.fixture
def mock_early_hints_response():
    return MagicMock()


def test_return_response_headers(mock_response_headers):
    returned = mock_response_headers.return_response_headers()

    mock_headers = 'HTTP/1.1 200 hello\r\nDate: 1/1/2020\r\nServer: 0.0.0.0\r\nContent-Type: plain\r\nConnection: keep-alive\r\n\r\n'

    assert returned == mock_headers

# def test_get_headers(mock_response):
#     headers = mock_response.get_headers(0)

#     assert mock_response.status_code == headers.status_code
#     assert mock_response.status_message == headers.status_message
#     assert mock_response.server == headers.server
#     assert mock_response.content_type == headers.content_type


def test_set_early_hints_header():
    early_hints_header = mock_early_hints_response._set_early_hints_header()

    assert early_hints_header == ""




