import json
from pprint import pprint
import socket
from node import Node

BOOTSTRAP_NODE = ("localhost", 1234)


class KademliaProtocol:
    def __init__(self, sourceNode: Node):
        self.sourceNode = sourceNode
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("Starting Kademlia protocol on port {}.".format(sourceNode.port))
        self.transport.bind(("localhost", sourceNode.port))
        self.transport.setblocking(False)

    def join(self):
        self.find_node(self.sourceNode.id, BOOTSTRAP_NODE)

    def find_node(self, node_id, addr):
        self.transport.sendto(
            RPC.serialize(RPC.find_node(self.sourceNode.id, node_id)), addr
        )

    def ping(self, addr):
        self.transport.sendto(RPC.serialize(RPC.ping()), addr)

    def handle_find_node(self, node_id, addr):
        nodes = self.sourceNode.find_node(node_id)
        self.transport.sendto(
            RPC.serialize(RPC.handle_find_node(self.sourceNode.id, node_id, nodes)),
            addr,
        )

    def handle_ping(self, addr):
        self.transport.sendto(RPC.serialize(RPC.ping()), addr)

    def handle(self, data, addr):
        message = RPC.parse(data)
        if RPC.is_valid(message):
            self.sourceNode.update_kbuckets(message["source_node_id"], addr)
            pprint(self.sourceNode.kbuckets)
            if message["type"] == "find_node":
                self.handle_find_node(message["node_id"], addr)
            elif message["type"] == "ping":
                self.handle_ping(addr)
            else:
                print("Unknown message type: {}".format(message["type"]))

    def listen(self):
        while True:
            try:
                data, addr = self.transport.recvfrom(1024)
                self.handle(data, addr)
            except BlockingIOError:
                pass


class RPC:
    @staticmethod
    def find_node(source_node_id, node_id):
        return {
            "type": "find_node",
            "source_node_id": source_node_id,
            "node_id": node_id,
        }

    @staticmethod
    def handle_find_node(source_node_id, node_id, nodes):
        return {
            "type": "handle_find_node",
            "source_node_id": source_node_id,
            "node_id": node_id,
            "nodes": nodes,
        }

    @staticmethod
    def ping(source_node_id):
        return {"type": "ping", "source_node_id": source_node_id}

    @staticmethod
    def serialize(message):
        return json.dumps(message).encode("utf-8")

    @staticmethod
    def parse(data):
        return json.loads(data.decode("utf-8"))

    @staticmethod
    def is_valid(message):
        return "type" in message and message["type"] in [
            "find_node",
            "handle_find_node",
            "ping",
        ]
