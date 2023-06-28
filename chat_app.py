import sys
import time
from chat_protocol import ChatProtocol, send_session_sync
import threading
from protocol import KademliaProtocol

class ChatApp:
    def __init__(self, user_alias, port):
        self.port = port
        self.chat_protocol = ChatProtocol(user_alias, port)
        self.kademlia = KademliaProtocol(port)

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


# TODO GUI -> Protocol:
# createChatroom(chatRoomName, numberOfPeers) +++ DONE
# joinChatroom() +++ DONE
# leaveChatroom() +++ DONE
# sendMessage(sessionId, message)
# getMessage(sessionId) returns (sortierte Liste[timestamp, msg, userAlias])

# Message Array Format:
# [{"timestamp": 1234566123, "msg": "A", "alias": "Username1"},
# {"timestamp": 1234566123, "msg": "A", "alias": "Username1"}]


# TODO (Martin):
# - call sync_session in every couple seconds
# - make the dict thread safe
# - send and sync messages



# following stuff is just for testing
def test_closest_nodes():
    return [('127.0.0.1', 1234), ('127.0.0.1', 1235), ('127.0.0.1', 1236)]


def initiator(chat_app):
    chat_app.create_chat_room("Test-Session", test_closest_nodes())
    time.sleep(1)
    send_session_sync("42")


def leaver(chat_app, after_seconds):
    time.sleep(after_seconds)
    chat_app.leave_chat_room("42")


def joiner(chat_app):
    chat_app.join_chat_room()


def print_sessions_periodically(chat_app):
    chat_app.chat_protocol.print_sessions()
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
