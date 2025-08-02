import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
import asyncio
from hango.http import ResponseHeaders, Response, EarlyHintsResponse, HTTPRequestParser

@pytest.fixture
def mock_writer():
    return MagicMock()

@pytest.fixture
def mock_http_request_parser():
    mock_container = MagicMock()
    return HTTPRequestParser(container=mock_container)

@pytest.fixture
def mock_reader():
    return MagicMock()

@pytest.mark.asyncio
async def test__receive_byte_data(monkeypatch, mock_reader, mock_http_request_parser):
    mock_data = b'hello'
    monkeypatch.setattr(mock_reader, 'readuntil', AsyncMock(return_value=mock_data))
    returned = await mock_http_request_parser._receive_byte_data(mock_reader)

    assert returned in mock_data


def test__separate_lines_and_body(mock_http_request_parser):
    data = b'HTTP/1.1\r\n\r\nbody'
    headers, body = mock_http_request_parser._separate_lines_and_body(data)
    assert headers == b'HTTP/1.1'
    assert body == b'body'

def test_decode_header(mock_http_request_parser):
    data = "HTTP/1.1"
    raw_data = b"HTTP/1.1"
    returned = mock_http_request_parser._decode_header(raw_data)
    assert returned == data

def test__split_header_text(mock_http_request_parser):
    mock_header_text = "Attribute1: foo\r\n\r\nAttribute2: baz"
    returned = mock_http_request_parser._split_header_text(mock_header_text)
    assert returned == ["Attribute1: foo", "", "Attribute2: baz"]
