
class SessionStore:
    def __init__(self):
        self._client_data: dict[str, dict] = {}
 
    def get_session(self, session_id: str) -> dict:
        return self._client_data.setdefault(session_id, {})
    
    def exists(self, session_id: str) -> bool:
        return session_id in self._client_data
    
    def set_session(self, session_id: str, new_client_data) -> dict:
        self._client_data[session_id] = new_client_data

    

