import json
import socket
import threading
from datetime import datetime, timezone

sessions = dict()  # at one point it would be nice to make sure if accessing it is thread safe, probably important when the sending thread is introduced ...


class Session:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.peers = dict()
        self.msg_buf = []

    def __str__(self):
        return f"Session(id={self.id}, name={self.name}, peers={self.peers}, msg_buf={self.msg_buf})"


def handle_reject_session_creation(socket):
    socket.close()


def handle_accept_session_creation(session_id, socket):
    add_peer_to_session(session_id, socket)


def handle_session_creation(session_id, session_name, socket):
    print("Session-request received with ID: " + session_id + " from: " + str(socket.getpeername()))

    if True:  # TODO: async request to user if he wants to
        build_session(session_id, session_name)
        add_peer_to_session(session_id, socket)

        socket.send(RPC.serialize(RPC.accept_session_creation(session_id)))
    else:
        socket.send(RPC.serialize(RPC.reject_session_creation()))


def handle_session_sync(session_id, peers, msg_buf):
    peers_as_tuples = [tuple(item) for item in peers]
    session = sessions.get(session_id)
    if session:
        unknown_peers = set(peers_as_tuples) - set(session.peers.keys())
        connect_to_peers(unknown_peers, session)


def handle(data, socket):
    message = RPC.parse(data)
    if RPC.is_valid(message):
        if message["type"] == "session_creation":
            handle_session_creation(message["session_id"], message["session_name"], socket)
        elif message["type"] == "session_sync":
            handle_session_sync(message["session_id"], message["known_peers"], message["msg_buf"])
        elif message["type"] == "accept_session_creation":
            handle_accept_session_creation(message["session_id"], socket)
        elif message["type"] == "reject_session_creation":
            handle_reject_session_creation(socket)
        elif message["type"] == "ping":
            print("PING received on session " + message["session_id"] + " from " + socket.getpeername()[0]
                  + ":" + str(socket.getpeername()[1]))
        else:
            print("Unknown message type: {}".format(message["type"]))


def on_connection(socket):
    while True:
        try:
            data = socket.recv(1024)
            if data:
                handle(data, socket)
        except ConnectionResetError:
            socket.close()
            print("Connection closed by remote peer.")
            break


def session_creation(session_id, session_name, possible_peers):
    new_session = build_session(session_id, session_name)
    connect_to_peers(possible_peers, new_session, isCreation=True)


def session_sync(session_id):
    # idea is to execute that every couple seconds?
    session = sessions[session_id]
    if session:
        for s in session.peers.values():
            peers_as_list = [list(t) for t in session.peers.keys()]
            peers_as_list.remove(list(s.getpeername()))  # remove the peer you are talking to
            s.send(RPC.serialize(RPC.session_sync(session.id, peers_as_list, session.msg_buf)))


# TODO: util class?
def build_session(session_id, session_name):
    # TODO: maybe perform a lookup before creation?
    session = Session(session_id, session_name)
    sessions[session_id] = session

    return session


def add_peer_to_session(session_id, socket):
    session = sessions.get(session_id)
    if session:
        session.peers[socket.getpeername()] = socket


def connect_to_peers(peers, session, isCreation=False):
    for p in peers:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(p)
        except ConnectionRefusedError:
            continue

        if isCreation:
            s.send(RPC.serialize(RPC.session_creation(session.id, session.name)))
        else:
            add_peer_to_session(session.id, s)

        # start a thread for each established connection
        threading.Thread(target=on_connection, args=[s]).start()


class ChatProtocol:
    def __init__(self, port_number):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.bind(("localhost", port_number))
        print("Starting TCP Socket on port {}.".format(port_number))
        # self.transport.setblocking(False)

    def print_sessions(self):
        for s in sessions.values():
            print("Session: " + str(s))

    def listen(self):
        self.transport.listen()
        while True:
            s, _ = self.transport.accept()
            threading.Thread(target=on_connection, args=[s]).start()

    def send_msg(self, session_id, msg, sender):
        session_timestamp = datetime(2023, 1, 1, 12, 42, 59,
                                     tzinfo=timezone.utc)  # should be the timestamp set during chatroom creation
        local_time = datetime.now(timezone.utc)
        diff = local_time - session_timestamp
        offset = diff.total_seconds()  # use this value to sort incoming messages

        # TODO: iterate over existing TCP addrinfo and send message to each


class RPC:
    # For testing purposes
    @staticmethod
    def ping(session_id):
        return {
            "type": "ping",
            "session_id": session_id
        }

    @staticmethod
    def session_creation(session_id, session_name):
        return {
            "type": "session_creation",
            "session_id": session_id,
            "session_name": session_name,
        }

    @staticmethod
    def session_sync(session_id, known_peers, msg_buf):
        return {
            "type": "session_sync",
            "session_id": session_id,
            "known_peers": known_peers,
            "msg_buf": msg_buf
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
    def reject_session_creation():
        return {
            "type": "reject_session_creation",
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
            "session_sync",
            "ping"
            # TODO: rest nachtragen
        ]
