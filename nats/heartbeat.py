"heartbeat between client and server"

from nats.const import Const
from twisted.internet.task import LoopingCall
from nats.protocol import Protocol
import Queue

class Heartbeat(object):
    "heartbeat between client and server"

    def __init__(self, conn):
        self.pings = 0
        self.pongs = Queue.Queue(-1)
        self.pings_outstanding = 0
        self.pongs_received = 0
        #self.ping_interval = Const.DEFAULT_PING_INTERVAL
        #self.max_outstanding_pings = Const.DEFAULT_PING_MAX
        self.conn = conn
        self.worker = self.create()

    def send_ping(self):
        "send ping request to nats server"
        self.pings_outstanding += 1
        self.queue_server_rt(self.process_pong)
        self.conn.flush_pending()

    def on_ping_request(self):
        'handler when ping request received'
        self.pings += 1
        self.conn.send_command(Protocol.pong_response())

    def on_pong_response(self):
        'handler when pong response received'
        blk = self.pongs.get()
        if blk: 
            blk()

    def queue_server_rt(self, blk):
        'queue server response'
        if not blk: 
            return None
        self.pongs.put(blk)
        self.conn.send_command(Protocol.ping_request())

    def create(self):
        "create looping call to send ping request"
        return LoopingCall(self.send_ping)

    def start(self):
        'start ping timer'
        self.worker.start(Const.DEFAULT_PING_INTERVAL)
        
    def process_pong(self):
        "process pong response from nats server"
        self.pongs_received += 1
        self.pings_outstanding -= 1

    def cancel(self):
        'cancel heartbeat'
        self.worker.stop()

