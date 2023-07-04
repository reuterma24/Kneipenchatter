from pprint import pprint
from time import sleep
from protocol import KademliaProtocol
from node import Node
import threading
import sys


class App:
    def __init__(self, port):
        self.port = port
        self.protocol = KademliaProtocol(port)
        threading.Thread(target=self.protocol.listen).start()
        self.protocol.join()

    def find_closest_nodes(self, num_nodes):
        nodes = []
        for bucket in reversed(self.protocol.sourceNode.kbuckets):
            for node_id in self.protocol.sourceNode.kbuckets[bucket]:
                nodes.append(node_id)
                if len(nodes) == num_nodes:
                    return nodes
        return nodes

    def test_closest_nodes(self):
        return [{"u33dc1v0": ("127.0.0.1", 1234)}, {"u33dc1v0": {"127.0.0.1", 1235}}]

    # requested_peers = []
    # session = ["session1":[u3234":1,"u33123":1], "session2":[u3234":1,"u33123":1]
    # # 1. Request to closest node
    # 2. TCP connection to this node
    # 3. Send message to this node


if __name__ == "__main__":
    port = int(sys.argv[1])
    node = Node(ip="localhost", port=port, ksize=20, alpha=3)
    app = App(node)