from random import randrange

import geohash
import geocoder

KBUCKETS = 64


def random_id(lat, long, use_lat_long):
    """Generate a random 160-bit string."""
    if use_lat_long:
        return geohash.encode(lat, long, precision=8)
    else:
        return geohash.encode(randrange(50, 60), randrange(50, 60), precision=8)


# Convert a string to binary and return as one string
def convert_string_to_bits(s):
    """Convert a string to binary and return as one string."""
    return "".join(f"{ord(i):08b}" for i in s)


# Calculate longest common prefix length of two strings in bits
def longest_prefix_match(a, b):
    """Return the length of the longest common prefix of two strings."""
    a_bits = convert_string_to_bits(a)
    b_bits = convert_string_to_bits(b)
    count = 0
    for i in range(min(len(a_bits), len(b_bits))):
        if a_bits[i] == b_bits[i]:
            count += 1
        else:
            break
    return count


def distance(a, b):
    """Return the XOR distance between a and b."""
    a_bits = convert_string_to_bits(a)
    b_bits = convert_string_to_bits(b)
    return int(a_bits, 2) ^ int(b_bits, 2)


def get_location():
    try:
        location = geocoder.ip("me")
        return location.latlng
    except:
        return None


class Node:
    def __init__(self, ip, port, ksize, alpha):
        self.ip = ip
        self.port = port
        self.ksize = ksize
        self.alpha = alpha
        location = get_location()
        self.id = random_id(location[0], location[1], False)
        self.kbuckets = {}
        self.waiting = {}
        for i in range(KBUCKETS):
            self.kbuckets[i] = {}
            self.waiting[i] = {}

    def update_kbuckets(self, node_id, addr):
        """Update the k-buckets of this node."""
        if node_id == self.id:
            return
        kbucket = KBUCKETS - longest_prefix_match(self.id, node_id)
        print("Updating kbucket: {}".format(kbucket))
        print("Node id: {}".format(node_id))
        if node_id not in self.kbuckets[kbucket]:
            if len(self.kbuckets[kbucket]) < self.ksize:
                self.kbuckets[kbucket][node_id] = addr
            else:
                self.waiting[kbucket][node_id] = addr
        else:
            # Remove the node from kbucket and add it to the end
            self.kbuckets[kbucket].pop(node_id)
            self.kbuckets[kbucket][node_id] = addr

    def find_node(self, node_id) -> dict[str, tuple[str, int]]:
        """Find the k closest nodes to node_id. If corresponding k-bucket has fewer than k entries, return the k closest nodes from other k-buckets."""
        kbucket = KBUCKETS - longest_prefix_match(self.id, node_id)
        if len(self.kbuckets[kbucket]) >= self.ksize:
            return self.kbuckets[kbucket]

        # Find k closest nodes from other k-buckets.
        nodes = {}
        i = j = kbucket

        while len(nodes) < self.ksize:
            if i >= 0:
                for node in self.kbuckets[i]:
                    nodes[node] = self.kbuckets[i][node]
                i -= 1
            if j < 64:
                for node in self.kbuckets[j]:
                    nodes[node] = self.kbuckets[j][node]
                j += 1
            if i < 0 and j >= 64:
                break

        print("Nodes: {}".format(nodes))
        return nodes
