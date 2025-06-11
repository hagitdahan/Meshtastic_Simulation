import random

class Message:
    def __init__(self, source, destination,timestamp, ttl, message_id):
        self.source = source
        self.destination = destination
        self.timestamp = timestamp
        self.ttl = random.randint(3, 6)
        self.message_id = message_id
        self.active = False
        self.delivered = False
        self.expired = False

class MessageManager:
    def __init__(self):
        self.messages = []
        self.current_time = 0

    def generate_random_pairs(self, num_messages, node_ids):
        self.messages = []
        for i in range(num_messages):
            source, dest = random.sample(node_ids, 2)
            timestamp = random.randint(1, 50)
            ttl = random.randint(5, 15)
            msg = Message(source, dest, timestamp, ttl, i)
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
