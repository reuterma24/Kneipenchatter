import sys
from typing import List
from udp import UDPConnection
from protocol import RPC, RPCType
import geocoder


# Get latitude and longitude from current location
def get_location():
    try:
        location = geocoder.ip("me")
        return location.latlng
    except:
        return None


BOOTSTRAP_NODE = ("localhost", 1234)

peers = []

"JOIN: lat:1234, long:1234"


class Node:
    def __init__(self, port) -> None:
        self.location = get_location()
        self.peers = []
        self.port = port
        self.udp_connection = UDPConnection(port)

    def join(self, node: tuple = BOOTSTRAP_NODE):
        self.udp_connection.send(RPC(123, RPCType.JOIN, self.location), node)

    def receive_welcome(self, rpc: RPC):
        # Example: "RECEIVE_WELCOME: [(lat:1234,long:1234,ip:1234,port:1234),(lat:1234, long:1234, ip:1234, port:1234)]"
        print(rpc.data)
        print(f"Welcome to the chat room! You are connected to {self.peers}")

    def send_welcome(self, node: tuple):
        self.udp_connection.send(RPC(123, RPCType.SEND_WELCOME, self.peers), node)


if __name__ == "__main__":
    port = int(sys.argv[1])
    node = Node(port)
    if port != 1234:
        node.join()
    if port == 1234:
        node.peers = [(1, 2, 3, 4), (1, 2, 3, 4)]
        node.udp_connection.receive()
        node.send_welcome(("localhost", 1235))
