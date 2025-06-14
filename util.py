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


    



