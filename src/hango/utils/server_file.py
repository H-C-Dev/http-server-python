import os
from hango.config import STATIC_ROOT, SERVER_ROOT
from hango.http import NotFound, InternalServerError
from hango.constants import EXTENSION_TO_MIME

class ServeFile:

    def __concat_path(self, path: str) -> str:
        req_path = os.path.join(SERVER_ROOT, path.lstrip("/"))
        return req_path
    
    # normpath to remove /../ in path - filesystem to prevent client from gaining access from anything outside static
    def __normalise_path(self, req_path: str) -> str:
        norm_path = os.path.normpath(req_path)
        return norm_path
    
    def __formatted_path(self, path: str) -> str:
        concat_path = self.__concat_path(path)
        formatted_path = self.__normalise_path(concat_path)
        return formatted_path
    
    def __check_common_path(self, formatted_path: str):
        if os.path.commonpath([formatted_path, STATIC_ROOT]) != STATIC_ROOT:
            raise NotFound(f"{formatted_path} Not Found")

    def __get_file_content_type(self, path) -> str:
        i = len(path) - 1
        while i >= 0:
            if path[i] == ".":
                return self.__get_MIME(path[i:])
            i-= 1
        raise InternalServerError(f"Something went wrong while reading the file: {path}")
    
    def __get_MIME(self, extension) -> str:
        return EXTENSION_TO_MIME[extension] 
            
    def is_static_prefix(self, path: str) -> bool:
            if path.startswith("/static/"):
                return True
            return False
    
    def __pick_file(self, concat_path):
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
    
    def __is_file_present(self, path: str) -> str:
        formatted_path = self.__formatted_path(path)
        self.__check_common_path(formatted_path)
        is_File = os.path.isfile(formatted_path)
        return (is_File, formatted_path)

    def serve_static_file(self, path: str) -> bytes:
        (is_File, concat_path) = self.__is_file_present(path)
        if is_File:
            file_bytes = self.__pick_file(concat_path)
            content_type = self.__get_file_content_type(path)
            print(f"Returning file_bytes: {file_bytes}")
            return (file_bytes, content_type)
        else:
            raise NotFound(f"{path} Not Found")
            
