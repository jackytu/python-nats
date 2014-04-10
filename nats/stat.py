"statistics for data processed"
import json

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


    def query(self):
        'clear all the statistics'
        return json.dumps({
           'msgs_received': self.msgs_received,
           'msgs_sent': self.msgs_sent,
           'bytes_received': self.bytes_received,
           'bytes_sent': self.bytes_sent
        })
