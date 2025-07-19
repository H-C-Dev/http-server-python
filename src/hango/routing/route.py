from hango.http import NotFound
from hango.utils import ExtractParams

class Route:
    def __init__(self, template, handler, method, local_middlewares=[]):
        self.template = template
        self.handler = handler
        self.method = method.upper()
        self.local_middlewares = local_middlewares

class RouteToHandler:
    def __init__(self):
        self._routes = []
        self._extract_params_helper = ExtractParams()

    def add_route(self, template, handler, method, local_middlewares=[]):
        self._routes.append(Route(template, handler, method, local_middlewares))

    def __extract_params(self, path, template):
        parameters = self._extract_params_helper.extract_path_params(path, template)
        return parameters

    def match_handler(self, method, path):
        for route in self._routes:
            if route.method.upper() == method.upper():
                parameters = self.__extract_params(path, route.template)
                if isinstance(parameters, dict):
                    return (route.handler, parameters, route.local_middlewares)
        raise NotFound(f"{method} {path} Not Found")




    