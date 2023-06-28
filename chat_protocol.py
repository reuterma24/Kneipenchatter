import json


class ChatProtocol:
    pass


class RPC:
    @staticmethod
    def session_creation(session_id, session_name):
        return {
            "type": "session_creation",
            "session_id": session_id,
            "session_name": session_name,
        }

    @staticmethod
    def join_session(session_id):
        return {
            "type": "join_session",
            "session_id": session_id,
        }

    @staticmethod
    def accept_session_creation(session_id):
        return {
            "type": "accept_session_creation",
            "session_id": session_id,
        }

    @staticmethod
    def reject_session_creation(session_id):
        return {
            "type": "reject_session_creation",
            "session_id": session_id,
        }

    @staticmethod
    def msg_to_session(session_id, msg):
        return {
            "type": "msg_to_session",
            "session_id": session_id,
            "msg": msg,
        }

    @staticmethod
    def leave_session(session_id):
        return {
            "type": "leave_session",
            "session_id": session_id,
        }

    @staticmethod
    def close_session(session_id):
        return {
            "type": "close_session",
            "session_id": session_id,
        }

    @staticmethod
    def serialize(message):
        return json.dumps(message).encode("utf-8")

    @staticmethod
    def parse(data):
        return json.loads(data.decode("utf-8"))
