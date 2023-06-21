import json
import socket
from datetime import datetime, timezone


class Session:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.peers = []
        self.msg_buf = []


class ChatProtocol:
    sessions = []

    def __init__(self, port_number):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Starting TCP Socket on port {}.".format(port_number))
        self.transport.bind(("localhost", port_number))
        # self.transport.setblocking(False)

    def handle(self, data, addr):
        message = RPC.parse(data)
        if RPC.is_valid(message):
            if message["type"] == "session_creation":
                self.handle_session_creation(message["session_id"], message["session_name"])
            else:
                print("Unknown message type: {}".format(message["type"]))

    def listen(self):
        self.transport.listen()
        conn, _ = self.transport.accept()
        print("Vor While Loop")
        while True:
            print("Im While Loop")
            try:
                data, addr = conn.recvfrom(1024)
                if data:
                    self.handle(data, addr)
            except BlockingIOError:
                pass

    def handle_session_creation(self, session_id, session_name):
        print("session recieved: " + str(session_id) + "on port:" + str(self.transport.getsockname()[1]))
        self.sessions.append(Session(session_id, session_name))

    def session_creation(self, session_id, session_name, possible_peers):
        for ip, port in possible_peers:
            self.transport.connect((ip, port))
            self.transport.send(RPC.serialize(RPC.session_creation(session_id, session_name)))

    def send_msg(self, session_id, msg, sender):
        session_timestamp = datetime(2023, 1, 1, 12, 42, 59,
                                     tzinfo=timezone.utc)  # should be the timestamp set during chatroom creation
        local_time = datetime.now(timezone.utc)
        diff = local_time - session_timestamp
        offset = diff.total_seconds()  # use this value to sort incoming messages

        # TODO: iterate over existing TCP addrinfo and send message to each


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
    def msg_to_session(session_id, msg, time_offset, sender):
        return {
            "type": "msg_to_session",
            "session_id": session_id,
            "msg": msg,
            "time_offset": time_offset,
            "sender": sender,
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

    @staticmethod
    def is_valid(message):
        return "type" in message and message["type"] in [
            "session_creation",
            "accept_session_creation",
            "reject_session_creation",
            # TODO: rest nachtragen
        ]
