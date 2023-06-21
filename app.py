from pprint import pprint
from time import sleep
from protocol import KademliaProtocol
from node import Node
from chat_protocol import ChatProtocol
import threading
import sys


class App:
    def __init__(self, port): #rename to Node???
        self.port = port
        #self.protocol = KademliaProtocol(port)
        self.chat_protocol = ChatProtocol(port.port)
        #threading.Thread(target=self.protocol.listen).start()
        threading.Thread(target=self.chat_protocol.listen).start()
        #self.protocol.join()

    def find_closest_nodes(self, num_nodes):
        nodes = []
        for bucket in reversed(self.protocol.sourceNode.kbuckets):
            for node_id in self.protocol.sourceNode.kbuckets[bucket]:
                nodes.append(node_id)
                if len(nodes) == num_nodes:
                    return nodes
        return nodes

    def test_closest_nodes(self):
        return [('127.0.0.1', 1234)]

    # requested_peers = []
    # session = ["session1":[u3234":1,"u33123":1], "session2":[u3234":1,"u33123":1]
    # # 1. Request to closest node
    # 2. TCP connection to this node
    # 3. Send message to this node


if __name__ == "__main__":
    port = int(sys.argv[1])
    node = Node(ip="localhost", port=port, ksize=20, alpha=3)
    app = App(node)

    app.chat_protocol.session_creation(42, "Test-Session :)", app.test_closest_nodes())
