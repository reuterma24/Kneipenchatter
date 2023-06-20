import geohash
import geocoder

KBUCKETS = 65


def random_id(lat, long):
    """Generate a random 160-bit string."""
    return geohash.encode(lat, long, precision=8)


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
    return a ^ b


def get_location():
    try:
        location = geocoder.ip("me")
        return location.latlng
    except:
        return None


class Node:
    def __init__(self, ip, port, ksize, alpha, id="u33dc1v1"):
        self.ip = ip
        self.port = port
        self.ksize = ksize
        self.alpha = alpha
        location = get_location()
        self.id = id or random_id(location[0], location[1])
        self.kbuckets = {}
        self.waiting = {}
        for i in range(KBUCKETS):
            self.kbuckets[i] = {}
            self.waiting[i] = {}

    def update_kbuckets(self, node_id, addr):
        """Update the k-buckets of this node."""
        kbucket = longest_prefix_match(self.id, node_id)
        print("Updating kbucket: {}".format(kbucket))
        print("Node id: {}".format(node_id))
        if node_id not in self.kbuckets[kbucket]:
            if len(self.kbuckets[kbucket]) < self.ksize:
                self.kbuckets[kbucket][node_id] = addr
            else:
                self.waiting[kbucket][node_id] = addr

    def find_node(self, node_id):
        """Find the k closest nodes to node_id."""
        kbucket = longest_prefix_match(self.id, node_id)
        return self.kbuckets[kbucket]
