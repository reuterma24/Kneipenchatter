import sys
import time
from chat_protocol import ChatProtocol, Util
import threading
from protocol import KademliaProtocol


class ChatApp:
    def __init__(self, user_alias, port):
        self.port = port
        self.chat_protocol = ChatProtocol(user_alias, port)
        # self.kademlia = KademliaProtocol(port)

    def create_chat_room(self, chat_room_name, number_of_peers):
        # TODO: select number_of_peers from kbucket result
        # TODO: create random ID
        peers = []
        self.chat_protocol.send_session_creation("42", chat_room_name, test_closest_nodes())

    def leave_chat_room(self, chat_room_id):
        self.chat_protocol.send_leave_session(chat_room_id)

    def join_chat_room(self):
        # TODO: select reasonable amount from kbucket
        self.chat_protocol.send_join_session(test_closest_nodes())

    def send_message(self, session_id, msg):
        self.chat_protocol.send_msg(session_id, msg)

    def get_message(self, session_id, number_of_messages):
        Util.get_messages(session_id, number_of_messages)



# TODO (Martin):
# bug: two sockets are established between two clients due to sync message -- not super easy to fix
# - refactor + more efficient locking?


# following stuff is just for testing
def test_closest_nodes():
    return [('127.0.0.1', 1234), ('127.0.0.1', 1235), ('127.0.0.1', 1236)]


def initiator(chat_app):
    chat_app.create_chat_room("Test-Session", test_closest_nodes())


def leaver(chat_app, after_seconds):
    time.sleep(after_seconds)
    chat_app.leave_chat_room("42")


def joiner(chat_app):
    chat_app.join_chat_room()


def messenger(chat_app, counter):
    chat_app.send_message("42", "Test-Message " + str(counter))
    counter += 1
    if counter <= 7:
        threading.Timer(10, messenger, args=[chat_app, counter]).start()


def print_sessions_periodically(chat_app):
    Util.print_sessions()
    threading.Timer(10, print_sessions_periodically, args=[chat_app]).start()


if __name__ == "__main__":
    port = int(sys.argv[1])
    chatApp = ChatApp("User-" + str(port), port)
    print_sessions_periodically(chatApp)

    if len(sys.argv) > 2:
        role = sys.argv[2]
        if role == "i":
            initiator(chatApp)
        elif role == "l":
            leaver(chatApp, 25)
        elif role == "j":
            joiner(chatApp)
        elif role == "m":
            messenger(chatApp, 0)
