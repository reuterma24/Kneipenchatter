import sys
import time
from protocol import KademliaProtocol
from chat_protocol import ChatProtocol, send_session_sync
import threading


class ChatApp:
    def __init__(self, port):
        self.port = port
        self.chat_protocol = ChatProtocol(port)
        self.kademlia = None  # TODO: init Kademlia after refactoring
        threading.Thread(target=self.chat_protocol.listen).start()


# TODO GUI -> Protocol:
# createChatroom(chatRoomName, numberOfPeers) # Wähle eine random ID..
# joinChatroom() #auto Join the closest existing peer --> select peers from kademlia
# leaveChatroom()
# sendMessage(sessionId, message)
# getMessage(sessionId) returns (sortierte Liste[timestamp, msg, userAlias])

# Message Array Format:
# [{"timestamp": 1234566123, "msg": "A", "alias": "Username1"},
# {"timestamp": 1234566123, "msg": "A", "alias": "Username1"}]


# TODO: init Kademlia in chatProtocol ctor()


# following stuff is just for testing
def test_closest_nodes():
    return [('127.0.0.1', 1234), ('127.0.0.1', 1235), ('127.0.0.1', 1236)]


def initiator(chat_protocol):
    chat_protocol.send_session_creation("43", "Test-Session", test_closest_nodes())
    time.sleep(1)
    send_session_sync("43")


def leaver(chat_protocol, after_seconds):
    time.sleep(after_seconds)
    chat_protocol.send_leave_session("43")


def print_sessions_periodically(chat_protocol):
    chat_protocol.chat_protocol.print_sessions()
    threading.Timer(10, print_sessions_periodically, args=[chat_protocol]).start()


if __name__ == "__main__":
    chatApp = ChatApp(int(sys.argv[1]))
    print_sessions_periodically(chatApp)

    initiator(chatApp.chat_protocol)
    # leaver(chatApp.chat_protocol, 25)
