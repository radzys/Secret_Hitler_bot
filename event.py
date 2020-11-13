class Event:
    def __init__(self, type, peer_id, from_id, text=None):
        self.type = type
        self.peer_id = peer_id
        self.from_id = from_id
        self.text = text