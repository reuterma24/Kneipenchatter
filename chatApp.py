import sys
import time

from chat_protocol import ChatProtocol, session_creation, session_sync
import threading


class ChatApp:
    def __init__(self, port):
        self.port = port
        self.chat_protocol = ChatProtocol(port)
        threading.Thread(target=self.chat_protocol.listen).start()


def test_closest_nodes():
    return [('127.0.0.1', 1234), ('127.0.0.1', 1235), ('127.0.0.1', 1236)]


def initiator():
    session_creation("43", "Test-Session :)", test_closest_nodes())
    time.sleep(1)
    session_sync("43")


if __name__ == "__main__":
    chatApp = ChatApp(int(sys.argv[1]))
    threading.Timer(20, chatApp.chat_protocol.print_sessions).start()


    initiator()
