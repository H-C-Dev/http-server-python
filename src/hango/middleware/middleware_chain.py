import asyncio

class MiddlewareChain:
    def __init__(self):
        self.global_middlewares = []
        self._hook_before_each_handler = []
        self._hook_after_each_handler = []
    

    def add_hook_before_each_handler(self, func):
        self._hook_before_each_handler.append(func)
        return func
    
    def add_hook_after_each_handler(self, func):
        self._hook_after_each_handler.append(func)
        return func

    def add_middleware(self, middleware):
        self.global_middlewares.append(middleware)

    def wrap_handler(self, handler, local_middlewares, request):

        for hook in self._hook_before_each_handler:
            hook(request)

        wrapped = handler
        for global_middleware in self.global_middlewares:
            wrapped = global_middleware(wrapped)

        for local_middleware in local_middlewares:
            wrapped = local_middleware(wrapped)
        return wrapped
    
    async def wrap_response(self, request, formatted_response):
        for hook in self._hook_after_each_handler:
            result = hook(request, formatted_response)
            if asyncio.iscoroutine(result):
                await result
            return result
