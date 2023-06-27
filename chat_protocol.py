import json
import socket
import threading
from datetime import datetime, timezone

sessions = dict()  # There are threads reading from it and there are threads modifying the content. Might have to implement a lock at some point


class Session:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.peers = dict()  # mapping of ("127.0.0.1", 1234) -> open socket-object
        self.msg_buf = []

    def __str__(self):
        return f"Session(id={self.id}, name={self.name}, peers={self.peers.keys()}, msg_buf={self.msg_buf})"


def handle_reject_session_creation(socket):
    socket.close()


def handle_accept_session_creation(session_id, socket):
    Util.add_peer_to_session(session_id, socket.getpeername(), socket)


def handle_session_creation(session_id, session_name, creator_address, socket):
    print("Session-request received with ID: " + session_id + " from: " + str(creator_address))

    if True:  # TODO: add async request to user if he wants to or maybe add to a list and creator keeps chatroom open until ppl join
        Util.build_session(session_id, session_name)
        Util.add_peer_to_session(session_id, tuple(creator_address), socket)

        socket.send(RPC.serialize(RPC.accept_session_creation(session_id)))
    else:
        socket.send(RPC.serialize(RPC.reject_session_creation()))
        socket.close()


def handle_leave_session(session_id, address):
    if session_id in sessions:
        session = sessions[session_id]
        del session.peers[tuple(address)]


def handle_session_sync(session_id, peers, msg_buf):
    peers_as_tuples = [tuple(item) for item in peers]
    session = sessions.get(session_id)
    if session:
        unknown_peers = set(peers_as_tuples) - set(session.peers.keys())
        Util.connect_to_peers(unknown_peers, session)


def handle(data, socket):
    message = RPC.parse(data)
    if RPC.is_valid(message):
        if message["type"] == "session_creation":
            handle_session_creation(message["session_id"], message["session_name"], message["creator_address"], socket)
        elif message["type"] == "session_sync":
            handle_session_sync(message["session_id"], message["known_peers"], message["msg_buf"])
        elif message["type"] == "accept_session_creation":
            handle_accept_session_creation(message["session_id"], socket)
        elif message["type"] == "reject_session_creation":
            handle_reject_session_creation(socket)
        elif message["type"] == "leave_session":
            handle_leave_session(message["session_id"], message["address"])
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
        except (ConnectionResetError, ConnectionAbortedError):
            socket.close()
            print("Connection closed to peer.")
            break


def send_session_sync(session_id):
    # idea is to execute that every couple seconds?
    # Idea: drop peers from session object if the socket is not open anymore?
    session = sessions[session_id]
    if session:
        for s in session.peers.values():
            peers_as_list = [list(k) for k, v in session.peers.items() if v != s]  # remove the peer you are talking to
            s.send(RPC.serialize(RPC.session_sync(session.id, peers_as_list, session.msg_buf)))


class ChatProtocol:
    def __init__(self, port_number):
        self.address = ('127.0.0.1', port_number)
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.bind(self.address)
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

    def send_session_creation(self, session_id, session_name, possible_peers):
        session = Util.build_session(session_id, session_name)
        for p in possible_peers:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect(p)
            except ConnectionRefusedError:
                continue

            s.send(RPC.serialize(RPC.session_creation(session.id, session.name, self.address)))

            # start a thread for each established connection
            threading.Thread(target=on_connection, args=[s]).start()

    def send_leave_session(self, session_id):
        if session_id in sessions:
            session = sessions.pop(session_id)
            for s in session.peers.values():
                s.send(RPC.serialize(RPC.leave_session(session_id, self.address)))
                s.close()

    def send_msg(self, session_id, msg, sender):
        session_timestamp = datetime(2023, 1, 1, 12, 42, 59,
                                     tzinfo=timezone.utc)  # should be the timestamp set during chatroom creation
        local_time = datetime.now(timezone.utc)
        diff = local_time - session_timestamp
        offset = diff.total_seconds()  # use this value to sort incoming messages

        # TODO: iterate over existing TCP addrinfo and send message to each


class Util:
    @staticmethod
    def build_session(session_id, session_name):
        session = Session(session_id, session_name)
        sessions[session_id] = session

        return session

    @staticmethod
    def add_peer_to_session(session_id, key, socket):
        session = sessions.get(session_id)
        if session:
            session.peers[key] = socket

    @staticmethod
    def connect_to_peers(peers, session):
        for p in peers:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect(p)
            except ConnectionRefusedError:
                continue

            Util.add_peer_to_session(session.id, s.getpeername(), s)

            # start a thread for each established connection
            threading.Thread(target=on_connection, args=[s]).start()


class RPC:
    # For testing purposes
    @staticmethod
    def ping(session_id):
        return {
            "type": "ping",
            "session_id": session_id
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
    def leave_session(session_id, address):
        return {
            "type": "leave_session",
            "session_id": session_id,
            "address": address
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
            "leave_session",
            "ping"
            # TODO: rest nachtragen
        ]
