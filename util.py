import os
from config import SERVER_ROOT
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
    
    def __concat_directory(self, path: str) -> str:
        file_path = SERVER_ROOT + path
        print(f"Client is requesting: {file_path}")
        return file_path
    
    def __is_file_present(self, path: str) -> str:
        concat_directory = self.__concat_directory(path)
        isFile = os.path.isfile(concat_directory)
        return isFile
    
    def is_static_prefix(self, path: str) -> bool:
            if path.startswith("/static/"):
                return True
            return False

    def serve_static_file(self, path: str):
        # check if the file exists
        if self.__is_file_present(path):
        # if yes -> return the file
            print(True)
            pass
        else:
        # if no -> return 404
            print(False)
            pass
            
  



