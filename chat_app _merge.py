import sys
import time
from chat_protocol import ChatProtocol, Util
import threading
from kademlia.protocol import KademliaProtocol


class ChatApp:
    def __init__(self, user_alias, port):
        self.port = port
        self.chat_protocol = ChatProtocol(user_alias, port)
        self.kademlia = KademliaProtocol(port)

    def create_chat_room(self, chat_room_name, number_of_peers):
        # TODO: select number_of_peers from kbucket result
        peers = []
        # id = Util.create_random_session_id()
        self.chat_protocol.send_session_creation(RANDOM_ID, chat_room_name, test_closest_nodes())

    def leave_chat_room(self, chat_room_id):
        self.chat_protocol.send_leave_session(chat_room_id)

    def join_chat_room(self):
        # TODO: select reasonable amount from kbucket
        self.chat_protocol.send_join_session(test_closest_nodes())

    def send_message(self, session_id, msg):
        self.chat_protocol.send_msg(session_id, msg)

    def get_messages(self, session_id, number_of_messages):
        Util.get_messages(session_id, number_of_messages)


