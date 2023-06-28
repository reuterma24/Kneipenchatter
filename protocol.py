import json
from pprint import pprint
import socket
import threading
import time
from node import Node, longest_prefix_match, KBUCKETS

BOOTSTRAP_NODE = ("localhost", 1234)


class KademliaProtocol:
    def __init__(self, port, ksize=20, alpha=3):
        self.sourceNode = Node(ip="localhost", port=port, ksize=ksize, alpha=alpha)
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("Starting Kademlia protocol on port {}.".format(port))
        self.transport.bind(("localhost", port))
        self.transport.setblocking(False)
        self.handle_find_node_calls = {}
        threading.Thread(target=self.listen).start()
        time.sleep(1)
        self.join()
        time.sleep(1)
        self.find_nearest_nodes(self.sourceNode.id)

    def join(self):
        if self.sourceNode.port == 1234:
            return
        print("Joining the network.")
        self.find_node(self.sourceNode.id, BOOTSTRAP_NODE)
        print("Joined the network.")

    def find_node(self, node_id, addr):
        self.transport.sendto(
            RPC.serialize(RPC.find_node(self.sourceNode.id, node_id)), addr
        )

    def find_nearest_nodes(self, node_id):
        print("Finding nearest nodes to {}".format(node_id))
        current_nearest_nodes = self.sourceNode.find_node(node_id)
        asked_nodes = {}
        print("Current nearest nodes: {}".format(current_nearest_nodes))
        # Choose alpha nodes from the current nearest nodes
        alpha_nodes = {}
        while current_nearest_nodes:
            for i in range(self.sourceNode.alpha):
                if len(current_nearest_nodes) == 0:
                    break
                key, value = current_nearest_nodes.popitem()
                alpha_nodes[key] = value
            asked_nodes.update(alpha_nodes)
            # Send find_node RPCs to alpha nodes
            for alpha_node in alpha_nodes:
                addr = tuple(alpha_nodes[alpha_node])
                print("Sending find_node to {}".format(addr))
                self.find_node(node_id, addr)

            TIMEOUT_SECONDS = 5
            passed_time = 0
            reached_nodes = 0
            while passed_time < TIMEOUT_SECONDS and reached_nodes < len(alpha_nodes):
                print(f"{reached_nodes} out of {len(alpha_nodes)} reached")
                for alpha_node in alpha_nodes:
                    if alpha_node in self.handle_find_node_calls.keys():
                        reached_nodes += 1
                        print("Received find_node response from {}".format(alpha_node))
                        recieved_nodes = self.handle_find_node_calls[alpha_node]
                        pprint(f"Recieved nodes: {recieved_nodes} from {alpha_node}")
                        del self.handle_find_node_calls[alpha_node]
                        for recieved_node in recieved_nodes:
                            if (
                                len(current_nearest_nodes) < self.sourceNode.ksize
                                and recieved_node not in asked_nodes.keys()
                            ):
                                current_nearest_nodes[recieved_node] = recieved_nodes[
                                    recieved_node
                                ]
                                continue
                            for asked_node in asked_nodes:
                                is_distance_smaller = longest_prefix_match(
                                    recieved_node, node_id
                                ) < longest_prefix_match(asked_node, node_id)
                                if (
                                    is_distance_smaller
                                    and recieved_node not in asked_nodes.keys()
                                ):
                                    current_nearest_nodes[
                                        recieved_node
                                    ] = recieved_nodes[recieved_node]
                                    print(
                                        "Distance to {} is smaller than distance to {}".format(
                                            recieved_node, asked_node
                                        )
                                    )
                                    pprint(
                                        "Current nearest nodes: {}".format(
                                            current_nearest_nodes
                                        )
                                    )
                                    break
                time.sleep(1)
                passed_time += 1
            alpha_nodes = {}
        print("kbuckets: {}".format(self.sourceNode.kbuckets))
        return current_nearest_nodes

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
            if message["type"] == "find_node":
                print("Received find_node from {}".format(addr))
                self.handle_find_node(message["node_id"], addr)
            elif message["type"] == "ping":
                print("Received ping from {}".format(addr))
                self.handle_ping(addr)
            elif message["type"] == "handle_find_node":
                self.handle_find_node_calls[message["source_node_id"]] = message[
                    "nodes"
                ]
                print("Found nodes: {}".format(message["nodes"]))
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
