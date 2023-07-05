import socket
import threading
import hashlib
import uuid
from datetime import datetime, timezone
from chat_protocol_resources import Session, RPC, MSG_BUFFER_SIZE, MSG_BUFFER_SYNC_THRESHOLD, SYNC_INTERVAL


sessions = dict()
lock = threading.Lock()


def handle(data, socket):
    messages = RPC.parse(data)
    for message in messages:
        if RPC.is_valid(message):
            if message["type"] == "session_creation":
                handle_session_creation(message["session_id"], message["session_name"], message["creator_address"],
                                        socket)
            elif message["type"] == "accept_session_creation":
                handle_accept_session_creation(message["session_id"], socket)
            elif message["type"] == "reject_session_creation":
                handle_reject_session_creation(socket)
            elif message["type"] == "join_session":
                handle_join_session(message["address"], socket)
            elif message["type"] == "leave_session":
                handle_leave_session(message["session_id"], message["address"])
            elif message["type"] == "session_sync":
                handle_session_sync(message["session_id"], message["session_name"], message["known_peers"])
            elif message["type"] == "chat_sync":
                handle_chat_sync(message["session_id"], message["session_name"], message["messages"])
            elif message["type"] == "msg_to_session":
                handle_message(message["session_id"], message["timestamp"], message["msg"], message["user_alias"])
            elif message["type"] == "ping":
                pass  # print("PING received on session from " + str(socket.getpeername()))
            else:
                print("Unknown message type: {}".format(message["type"]))


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


def handle_session_sync(session_id, session_name, peers):
    session = Util.resolve_session(session_id, session_name)
    with lock:
        peers_as_tuples = [tuple(item) for item in peers]
        unknown_peers = set(peers_as_tuples) - set(session.peers.keys())
    for p in unknown_peers:
        socket = Util.connect_and_handle(p)
        if socket:
            Util.add_peer_to_session(session.id, socket.getpeername(), socket)


def handle_chat_sync(session_id, session_name, messages):
    session = Util.resolve_session(session_id, session_name)
    messages_as_dict = [dict(message) for message in messages]
    Util.add_messages(session.id, messages_as_dict)


def handle_message(session_id, timestamp, msg, user_alias):
    if session_id in sessions:
        message = Util.build_message(timestamp, msg, user_alias)
        Util.add_message(session_id, message)


def sync():
    for session in sessions.values():
        try:
            Util.sanitize_peers(session.peers)
            send_session_sync(session)
            send_chat_sync(session)
        except (ConnectionResetError, ConnectionAbortedError, OSError):
            pass  # just to be safe - if unlucky timing a connection might be closed immediately after sanitize_peers()

    threading.Timer(SYNC_INTERVAL, sync).start()


def send_session_sync(session):
    with lock:
        for k, socket in session.peers.items():
            peers_as_list = [list(k) for k, v in session.peers.items() if
                             v != socket]  # remove the peer you are talking to
            socket.send(RPC.serialize(RPC.session_sync(session.id, session.name, peers_as_list)))


def send_chat_sync(session):
    recent_messages = Util.get_messages(session.id, MSG_BUFFER_SYNC_THRESHOLD)
    with lock:
        for socket in session.peers.values():
            socket.send(RPC.serialize(RPC.chat_sync(session.id, session.name, recent_messages)))


class ChatProtocol:
    def __init__(self, user_alias, port_number):
        self.user_alias = user_alias
        self.address = ('127.0.0.1', port_number)
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.bind(self.address)
        print("Starting TCP Socket on port {}.".format(port_number))
        threading.Thread(target=self.listen).start()
        threading.Thread(target=sync).start()

    def listen(self):
        self.transport.listen()
        while True:
            s, _ = self.transport.accept()
            threading.Thread(target=Util.on_connection, args=[s]).start()

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

    def send_msg(self, session_id, msg):
        if session_id in sessions:
            message = Util.build_message(Util.create_timestamp(), msg, self.user_alias)
            Util.add_message(session_id, message)
            with lock:
                for socket in sessions[session_id].peers.values():
                    try:
                        socket.send(RPC.serialize(RPC.msg_to_session(session_id, message["timestamp"], message["msg"], message["user_alias"])))
                    except (ConnectionResetError, ConnectionAbortedError, OSError):
                        print("Connection to peer closed.")
                        pass  # just to be safe - if unlucky timing a connection might be closed immediately after sanitize_peers()

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
        print("Connection to new peer " + str(socket.getpeername()) + " established!")
        while True:
            try:
                data = socket.recv(4096)
                if data:
                    handle(data, socket)
            except (ConnectionResetError, ConnectionAbortedError, OSError):
                socket.close()
                print("Connection to peer closed.")
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

    @staticmethod
    def create_timestamp():
        return int(datetime.now(timezone.utc).timestamp())

    @staticmethod
    def create_random_session_id():
        return str(uuid.uuid4())

    @staticmethod
    def build_message(timestamp, msg, user_alias):
        hash_input = str(timestamp) + msg + user_alias
        hash = hashlib.md5(hash_input.encode(), usedforsecurity=False).hexdigest()
        return dict(timestamp=timestamp, msg=msg, user_alias=user_alias, hash=hash)

    @staticmethod
    def add_message(session_id, message):
        if session_id in sessions:
            with lock:
                buffer = sessions[session_id].msg_buf
                size = len(buffer)
                index = 0
                while index < size and buffer[index]["timestamp"] <= message["timestamp"]:
                    index += 1
                buffer.insert(index, message)
                if size + 1 > MSG_BUFFER_SIZE:
                    buffer.pop(0)

    @staticmethod
    def add_messages(session_id, messages):  # could be improved since they are ordered by timestamp
        if session_id in sessions:
            with lock:
                buffer = sessions[session_id].msg_buf
                incoming_hashes = {m["hash"] for m in messages}
                known_hashes = {m["hash"] for m in buffer}
                unknown_hashes = incoming_hashes.difference(known_hashes)
                unknown_messages = [m for m in messages if m["hash"] in unknown_hashes]
            for m in unknown_messages:
                Util.add_message(session_id, m)

    @staticmethod
    def get_messages(session_id, n):
        if session_id in sessions:
            with lock:
                buffer = sessions[session_id].msg_buf
                return list(buffer)[-n:]  # TODO: Don't think a deep copy is necessary if passed to GUI - we will see
