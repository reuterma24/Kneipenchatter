import socket

from protocol import RPC


class UDPConnection:
    def __init__(self, port: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("localhost", port))

    def send(self, message: RPC, node: tuple):
        self.sock.sendto(message.serialize().encode(), node)

    def receive(self):
        data, addr = self.sock.recvfrom(1024)
        msg = data.decode()
        print(f"Received {msg} from {addr}")
        return RPC.deserialize(msg), addr

    def close(self):
        self.sock.close()
