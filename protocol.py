from enum import Enum


class RPC:
    def __init__(self, sender_id, rpc_type, data=""):
        self.sender_id = sender_id
        self.rpc_type = rpc_type
        self.data = data

    def serialize(self):
        return f"{self.sender_id} {self.rpc_type} {self.data}"

    @staticmethod
    def deserialize(string):
        sender_id, rpc_type, data = string.split(" ", 2)
        return RPC(int(sender_id), rpc_type, data)


class RPCType(Enum):
    PING = (1,)
    JOIN = (2,)
    LEAVE = (3,)
    CHAT = (4,)
    SEND_WELCOME = (5,)
    RECEIVE_WELCOME = (6,)
