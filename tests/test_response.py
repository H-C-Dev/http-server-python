import pytest
from hango.server import HTTPServer, Server
from unittest.mock import AsyncMock, MagicMock, Mock
import asyncio
from hango.http import ResponseHeaders


@pytest.fixture
def mock_response_headers():
    return ResponseHeaders(status_code=200, status_message="hello", date="1/1/2020", server="0.0.0.0", content_length=0, content_type="plain")


def test_return_response_headers(mock_response_headers):
    returned = mock_response_headers.return_response_headers()


    mock_headers = 'HTTP/1.1 200 hello\r\nDate: 1/1/2020\r\nServer: 0.0.0.0\r\nContent-Type: plain\r\nConnection: keep-alive\r\n\r\n'
    
    assert returned == mock_headers