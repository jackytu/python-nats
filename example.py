import sys, time
from nats.client import NatsClient

NATS_URI = "nats://nats:nats@127.0.0.1:4222"

def main():
    nats = NatsClient()
    conn, error  = nats.connect_nats({
        "uri" : NATS_URI }
    )

    if error: sys.exit(-1)

    time.sleep(1)

    def request_cb(msg, reply):
        print  "received {}".format(msg)
        nats.publish(reply, "I can help!")

    def subscribe_cb(msg):
        print "received {}".format(msg)

    def publish_cb():
        print "published one message"

    sid = nats.subscribe("help", {}, request_cb)
    nats.publish("help", "who can help", "", publish_cb)
    nats.request("help", "who can help", {}, subscribe_cb)
    time.sleep(1)
    nats.unsubscribe(sid)
    
if __name__ == '__main__':
    main()
