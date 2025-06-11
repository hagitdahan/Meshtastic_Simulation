import random

class Message:
    def __init__(self, message_id, source, destination, timestamp):
        self.message_id = message_id
        self.source = source
        self.destination = destination
        self.timestamp = timestamp
        self.ttl = random.randint(3, 6)
        self.active = False
        self.delivered = False
        self.expired = False

class MessageManager:
    def __init__(self):
        self.messages = []
        self.current_time = 0

    def generate_random_pairs(self, num_messages, node_ids, simultaneous=True):
        self.messages = []
        used_pairs = set()
        for i in range(num_messages):
            while True:
                source = random.choice(node_ids)
                destination = random.choice(node_ids)
                if source != destination and (source, destination) not in used_pairs:
                    used_pairs.add((source, destination))
                    break
            timestamp = 0 if simultaneous else i  # messages released all at once or one-by-one
            msg = Message(message_id=i, source=source, destination=destination, timestamp=timestamp)
            self.messages.append(msg)

    def advance_time(self):
        self.current_time += 1
        for msg in self.messages:
            if not msg.delivered and not msg.expired:
                if self.current_time >= msg.timestamp:
                    msg.active = True

    def get_active_messages(self):
        return [msg for msg in self.messages if msg.active and not msg.delivered and not msg.expired]

    def mark_delivered(self, msg):
        msg.delivered = True
        msg.active = False

    def mark_expired(self, msg):
        msg.expired = True
        msg.active = False
