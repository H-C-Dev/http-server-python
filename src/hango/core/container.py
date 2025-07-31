class ServiceContainer:
    def __init__(self):
        self._services = {}

    def register(self, interface, implementation):
        self._services[interface] = implementation

    def get(self, interface):
        return self._services.get(interface)