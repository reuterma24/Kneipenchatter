import json
import socket
import threading
from datetime import datetime, timezone

sessions = dict()
lock = threading.Lock()


class Session:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.peers = dict()  # mapping of ("127.0.0.1", 1234) -> open socket-object
        self.msg_buf = []

    def __str__(self):
        return f"Session(id={self.id}, name={self.name}, peers={self.peers.keys()}, msg_buf={self.msg_buf})"


def handle_session_creation(session_id, session_name, creator_address, socket):
    if True:  # TODO: add async request to user if he wants to or maybe add to a list and creator keeps chatroom open until ppl join
        Util.resolve_session(session_id, session_name)
        Util.add_peer_to_session(session_id, tuple(creator_address), socket)

        socket.send(RPC.serialize(RPC.accept_session_creation(session_id)))
    else:
        socket.send(RPC.serialize(RPC.reject_session_creation()))
        socket.close()


def handle_accept_session_creation(session_id, socket):
    Util.add_peer_to_session(session_id, socket.getpeername(), socket)


def handle_reject_session_creation(socket):
    socket.close()


def handle_join_session(address, socket):
    if len(sessions) > 0:
        with lock:
            session = next(iter(sessions.values()))  # we just add to the first session available - silly deadlines :x
        if session:
            Util.add_peer_to_session(session.id, tuple(address), socket)
    else:
        socket.close()


def handle_leave_session(session_id, address):
    if session_id in sessions:
        with lock:
            session = sessions[session_id]
            del session.peers[tuple(address)]


def handle_session_sync(session_id, session_name, peers, msg_buf):
    peers_as_tuples = [tuple(item) for item in peers]
    session = Util.resolve_session(session_id, session_name)
    if session:
        unknown_peers = set(peers_as_tuples) - set(session.peers.keys())  # TODO: need thread safety here maybe?
        for p in unknown_peers:
            socket = Util.connect_and_handle(p)
            if socket:
                Util.add_peer_to_session(session.id, socket.getpeername(), socket)


def handle(data, socket):
    message = RPC.parse(data)
    if RPC.is_valid(message):
        if message["type"] == "session_creation":
            handle_session_creation(message["session_id"], message["session_name"], message["creator_address"], socket)
        elif message["type"] == "session_sync":
            handle_session_sync(message["session_id"], message["session_name"], message["known_peers"],
                                message["msg_buf"])
        elif message["type"] == "accept_session_creation":
            handle_accept_session_creation(message["session_id"], socket)
        elif message["type"] == "reject_session_creation":
            handle_reject_session_creation(socket)
        elif message["type"] == "join_session":
            handle_join_session(message["address"], socket)
        elif message["type"] == "leave_session":
            handle_leave_session(message["session_id"], message["address"])
        elif message["type"] == "ping":
            # print("PING received on session from " + str(socket.getpeername()))
            pass
        else:
            print("Unknown message type: {}".format(message["type"]))


def send_session_sync(session):
    with lock:
        for k, socket in session.peers.items():
            peers_as_list = [list(k) for k, v in session.peers.items() if
                             v != socket]  # remove the peer you are talking to
            socket.send(RPC.serialize(RPC.session_sync(session.id, session.name, peers_as_list, session.msg_buf)))


def sync():
    for session in sessions.values():
        try:
            Util.sanitize_peers(session.peers)
            send_session_sync(session)
        except (ConnectionResetError, ConnectionAbortedError, OSError):
            pass  # just to be safe - if the timing is unlucky a connection might ce closed immediately after sanitize_peers()

    threading.Timer(5, sync).start()


class ChatProtocol:
    def __init__(self, user_alias, port_number):
        self.user_alias = user_alias
        self.address = ('127.0.0.1', port_number)
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.bind(self.address)
        print("Starting TCP Socket on port {}.".format(port_number))
        threading.Thread(target=self.listen).start()
        threading.Thread(target=sync).start()
        # self.transport.setblocking(False)

    def listen(self):
        self.transport.listen()
        while True:
            s, _ = self.transport.accept()

            threading.Thread(target=Util.on_connection, args=[s]).start()
            print("Connection to new peer " + str(s.getpeername()) + " established!")

    def send_session_creation(self, session_id, session_name, possible_peers):
        session = Util.resolve_session(session_id, session_name)
        for p in possible_peers:
            socket = Util.connect_and_handle(p)
            if socket:
                socket.send(RPC.serialize(RPC.session_creation(session.id, session.name, self.address)))

    def send_join_session(self, peers):
        for p in peers:
            socket = Util.connect_and_handle(p)
            if socket:
                socket.send(RPC.serialize(RPC.join_session(self.address)))

    def send_leave_session(self, session_id):
        if session_id in sessions:
            with lock:
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
    def print_sessions():
        with lock:
            for s in sessions.values():
                print("Session: " + str(s))

    @staticmethod
    def resolve_session(session_id, session_name):
        if session_id in sessions:
            with lock:
                return sessions[session_id]

        session = Session(session_id, session_name)
        sessions[session_id] = session
        return session

    @staticmethod
    def add_peer_to_session(session_id, key, socket):
        with lock:
            session = sessions.get(session_id)
            if session:
                session.peers[key] = socket

    @staticmethod
    def connect_and_handle(peer):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(peer)
        except ConnectionRefusedError:
            return None

        # start a thread for each established connection
        threading.Thread(target=Util.on_connection, args=[s]).start()
        return s

    @staticmethod
    def on_connection(socket):
        while True:
            try:
                data = socket.recv(1024)
                if data:
                    handle(data, socket)
            except (ConnectionResetError, ConnectionAbortedError, OSError):
                socket.close()
                print("Connection closed to peer.")
                break

    @staticmethod
    def sanitize_peers(peers):
        with lock:
            closed_sockets = []
            for key, socket in peers.items():
                try:
                    socket.send(RPC.serialize(RPC.ping()))
                except (ConnectionResetError, ConnectionAbortedError, OSError):
                    closed_sockets.append(key)

            for key in closed_sockets:
                del peers[key]


class RPC:
    # For testing purposes
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
    def session_sync(session_id, session_name, known_peers, msg_buf):
        return {
            "type": "session_sync",
            "session_id": session_id,
            "session_name": session_name,
            "known_peers": known_peers,
            "msg_buf": msg_buf
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
            "join_session",
            "ping"
            # TODO: rest nachtragen
        ]
