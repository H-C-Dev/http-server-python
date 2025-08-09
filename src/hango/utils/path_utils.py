from typing import Tuple
import os
from hango.core import STATIC_ROOT, SERVER_ROOT
from hango.custom_http import NotFound, InternalServerError
from hango.core import EXTENSION_TO_MIME
import re

class ExtractParams:
    def _split_slash(self, path: str) -> list[str]:
        path_arr = path.strip("/").split("/")
        return path_arr

    def _check_path_len(self, path_parts: list[str], template_parts: list[str]) -> bool:
        if len(path_parts) != len(template_parts):
            return False
        else:
            return True
    # zip path and template to see if their pattern are 
    def _get_parameters(self, path_parts: list[str], template_parts: list[str]) -> dict | None:
        parameters = dict()
        for path_part, template_part in zip(path_parts, template_parts):
            if template_part.startswith("{") and template_part.endswith("}"):
                parameter_name = template_part[1:-1]
                parameters[parameter_name] = path_part
            elif path_part != template_part:
                return None
        return parameters

    def extract_path_params(self, path: str, template: str) -> dict | None:
        path_parts = self._split_slash(path)
        template_parts = self._split_slash(template)
        if not self._check_path_len(path_parts, template_parts): return None
        parameters = self._get_parameters(path_parts, template_parts)
        return parameters

class ServeFile:

    def _concat_path(self, path: str) -> str:
        req_path = os.path.join(SERVER_ROOT, path.lstrip("/"))
        return req_path
    
    # normpath to remove /../ in path - filesystem to prevent client from gaining access from anything outside static
    def _normalise_path(self, req_path: str) -> str:
        norm_path = os.path.normpath(req_path)
        return norm_path
    
    def _formatted_path(self, path: str) -> str:
        concat_path = self._concat_path(path)
        formatted_path = self._normalise_path(concat_path)
        return formatted_path
    
    def _check_common_path(self, formatted_path: str):
        if os.path.commonpath([formatted_path, STATIC_ROOT]) != STATIC_ROOT:
            raise NotFound(f"{formatted_path} Not Found")

    def _get_file_content_type(self, path) -> Tuple[str, bool]:
        i = len(path) - 1
        isHtml = False
        while i >= 0:
            if path[i] == ".":
                if path[i:] == ".html":
                    isHtml = True
                return (self._get_MIME(path[i:]), isHtml)
            i-= 1
        raise InternalServerError(f"Something went wrong while reading the file: {path}")
    
    def _get_MIME(self, extension) -> str:
        return EXTENSION_TO_MIME[extension] 
            
    def is_static_prefix(self, path: str) -> bool:
            if path.startswith("/static/"):
                return True
            return False
    
    def _pick_file(self, concat_path):
        # mutable byte array
        file = bytearray()
        with open(concat_path, "rb") as raw_file:
            while True:
                file_chunk = raw_file.read(4096)
                if not file_chunk:
                    break
                # to address the bytes immutable nature, use 'extend' on mutable byte array to prevent byte from creating new byte object to save memory.
                file.extend(file_chunk)
        return bytes(file)
    
    def _is_file_present(self, path: str) -> Tuple[bool, str]:
        formatted_path = self._formatted_path(path)
        self._check_common_path(formatted_path)
        is_File = os.path.isfile(formatted_path)
        return (is_File, formatted_path)
    
    def _extract_early_hints(self, html: str):
        css_links = re.findall(
            r'<link\b[^>]*\brel=["\']?stylesheet["\']?[^>]*\bhref=["\']([^"\']+)["\']',
            html,
            flags=re.IGNORECASE
        )

        js_srcs = re.findall(
            r'<script\b[^>]*\bsrc=["\']([^"\']+)["\']',
            html,
            flags=re.IGNORECASE
        )

        hints = []
        for href in css_links:
            hints.append({
                "url": href,
                "rel": "preload",
                "as": "style",
                "type": "text/css"
            })
        for src in js_srcs:
            hints.append({
                "url": src,
                "rel": "preload",
                "as": "script",
                "type": "application/javascript"
            })
        img_srcs = re.findall(
            r'<img\b[^>]*\bsrc=["\']([^"\']+)["\']',
            html,
            flags=re.IGNORECASE
        )
        for src in img_srcs:
            hints.append({
                "url": src,
                "rel": "preload",
                "as": "image",
                "type": "image"
            })
        return hints
    
    def _extract_html_early_hints_from_bytes(self, file_bytes):
        html = file_bytes.decode('utf-8')
        hints = self._extract_early_hints(html)
        return hints

    def serve_static_file(self, path: str) -> Tuple[bytes, str, list]:
        (is_File, concat_path) = self._is_file_present(path)
        if is_File:
            file_bytes = self._pick_file(concat_path)
            (content_type, isHtml)= self._get_file_content_type(path)
            hints = []
            if isHtml: 
                hints = self._extract_html_early_hints_from_bytes(file_bytes)
            print(f"Returning file_bytes: {file_bytes}")
            return (file_bytes, content_type, hints)
        else:
            raise NotFound(f"{path} Not Found")