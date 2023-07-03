import json

SEPARATOR = "|"

MSG_BUFFER_SIZE = 20
MSG_BUFFER_SYNC_THRESHOLD = 5
SYNC_INTERVAL = 5

class Session:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.peers = dict()  # mapping of ("127.0.0.1", 1234) -> open socket-object
        self.msg_buf = []  # array of mappings {"timestamp": int, "message": string, "user_alias": string, "hash": hash}

    def __str__(self):
        return f"Session(id={self.id}, name={self.name}, peers={self.peers.keys()}, msg_buf={self.msg_buf})"


class RPC:
    @staticmethod
    def ping():
        return {
            "type": "ping"
        }

    @staticmethod
    def session_creation(session_id, session_name, creator_address):
        return {
            "type": "session_creation",
            "session_id": session_id,
            "session_name": session_name,
            "creator_address": creator_address
        }

    @staticmethod
    def session_sync(session_id, session_name, known_peers):
        return {
            "type": "session_sync",
            "session_id": session_id,
            "session_name": session_name,
            "known_peers": known_peers
        }

    @staticmethod
    def chat_sync(session_id, session_name, messages):
        return {
            "type": "chat_sync",
            "session_id": session_id,
            "session_name": session_name,
            "messages": messages
        }

    @staticmethod
    def join_session(address):
        return {
            "type": "join_session",
            "address": address
        }

    @staticmethod
    def accept_session_creation(session_id):
        return {
            "type": "accept_session_creation",
            "session_id": session_id,
        }

    @staticmethod
    def reject_session_creation():
        return {
            "type": "reject_session_creation",
        }

    @staticmethod
    def msg_to_session(session_id, timestamp, msg, user_alias):
        return {
            "type": "msg_to_session",
            "session_id": session_id,
            "timestamp": timestamp,
            "msg": msg,
            "user_alias": user_alias,
        }

    @staticmethod
    def leave_session(session_id, address):
        return {
            "type": "leave_session",
            "session_id": session_id,
            "address": address
        }

    @staticmethod
    def serialize(message):
        content = json.dumps(message) + SEPARATOR
        return content.encode("utf-8")

    @staticmethod
    def parse(data):
        parsed_objects = []
        json_strings = data.decode("utf-8").split(SEPARATOR)[:-1]  # split and ignore last empty element
        for json_string in json_strings:
            try:
                parsed_objects.append(json.loads(json_string))
            except json.JSONDecodeError as e:
                print(f"JSON decoding error: {e}")
        return parsed_objects

    @staticmethod
    def is_valid(message):
        return "type" in message and message["type"] in [
            "session_creation",
            "accept_session_creation",
            "reject_session_creation",
            "session_sync",
            "leave_session",
            "join_session",
            "msg_to_session",
            "chat_sync",
            "ping"
        ]
