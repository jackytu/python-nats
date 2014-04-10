"statistics for data processed"

class Stat(object):
    "statistics for data processed"
    def __init__(self):
        self.msgs_received = 0
        self.msgs_sent = 0
        self.bytes_received = 0
        self.bytes_sent = 0

    def clear(self):
        'clear all the statistics'
        self.msgs_received = 0
        self.msgs_sent = 0
        self.bytes_received = 0
        self.bytes_sent = 0
