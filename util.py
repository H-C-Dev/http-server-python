import os
from config import SERVER_ROOT
from http_error import NotFound, InternalServerError
from response import CustomResponse
from constants import EXTENSION_TO_MIME
class ExtractParams:
    def __split_slash(self, path: str) -> list[str]:
        path_arr = path.strip("/").split("/")
        return path_arr

    def __check_path_len(self, path_parts: list[str], template_parts: list[str]) -> bool:
        if len(path_parts) != len(template_parts):
            return False
        else:
            return True
    # zip path and template to see if their pattern are 
    def __get_parameters(self, path_parts: list[str], template_parts: list[str]) -> dict | None:
        parameters = dict()
        for path_part, template_part in zip(path_parts, template_parts):
            if template_part.startswith("{") and template_part.endswith("}"):
                parameter_name = template_part[1:-1]
                parameters[parameter_name] = path_part
            elif path_part != template_part:
                return None
        return parameters

    def extract_path_params(self, path: str, template: str) -> dict | None:
        path_parts = self.__split_slash(path)
        template_parts = self.__split_slash(template)
        if not self.__check_path_len(path_parts, template_parts): return None
        parameters = self.__get_parameters(path_parts, template_parts)
        return parameters

class ServeFile:

    def __get_file_content_type(self, path) -> str:
        i = len(path) - 1
        while i >= 0:
            if path[i] == ".":
                return self.__get_MIME(path[i:])
            i-= 1
        raise InternalServerError("Something went wrong while reading the file: {path}")
    
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
        concat_path = SERVER_ROOT + path
        is_File = os.path.isfile(concat_path)
        return (is_File, concat_path)

    def serve_static_file(self, path: str) -> bytes:
        (is_File, concat_path) = self.__is_file_present(path)
        if is_File:
            file_bytes = self.__pick_file(concat_path)
            content_type = self.__get_file_content_type(path)
            print(f"Returning file_bytes: {file_bytes}")
            return CustomResponse(body=file_bytes, status_code=200, content_type=content_type)
        else:
            raise NotFound(f"{path} Not Found")
            
  



