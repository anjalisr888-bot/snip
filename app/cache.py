import threading


class Node:
    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRUCache:
    def __init__(self, capacity: int):
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self.capacity = capacity
        self.map = {}  # key -> Node
        # Dummy nodes so the list is never empty
        self.head = Node()  # most recent side
        self.tail = Node()  # least recent side
        self.head.next = self.tail
        self.tail.prev = self.head
        self.lock = threading.Lock()

    def _remove(self, node: Node) -> None:
        # Unlink node by connecting its neighbours to each other
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add_to_front(self, node: Node) -> None:
        # Insert node right after head
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def get(self, key):
        with self.lock:
            if key not in self.map:
                return None
            node = self.map[key]
            self._remove(node)
            self._add_to_front(node)
            return node.value

    def put(self, key, value) -> None:
        with self.lock:
            if key in self.map:
                self._remove(self.map[key])
            node = Node(key, value)
            self._add_to_front(node)
            self.map[key] = node

            if len(self.map) > self.capacity:
                lru = self.tail.prev
                self._remove(lru)
                del self.map[lru.key]

    def __len__(self):
        return len(self.map)