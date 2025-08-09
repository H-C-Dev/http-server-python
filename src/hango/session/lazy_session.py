import secrets

def generate_session_id():
    return secrets.token_hex(32)

class LazySession:
    def __init__(self, store, session_id=None, initial=None):
        self.store = store
        self.session_id = session_id if initial is not None else None
        self.data = initial or {}
        self.is_modified = False

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        if self.session_id is None:
            self.session_id = generate_session_id()
        self.data[key] = value
        self.is_modified = True

    def delete(self, key):
        if self.session_id is None:
            self.session_id = generate_session_id()
        if key in self.data:
            del self.data[key]
            self.is_modified = True
