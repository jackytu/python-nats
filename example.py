import time
from nats.client import NatsClient

NATS_URI = "nats://nats:nats@127.0.0.1:4222"

def main():
    nats = NatsClient(uris=NATS_URI)
    nats.start()
    time.sleep(1)

    def request_blk(msg, reply):
        print  "received {}".format(msg)
        nats.publish(reply, "dispatch some job to publishers!")

    def subscribe_blk(msg):
        print "received {}".format(msg)

    def publish_blk():
        print "callback after published one message"

    sid = nats.subscribe("job", subscribe_blk)
    nats.publish("job", "I have jobs", "", publish_blk)
    nats.request("job", "who has jobs", request_blk)
    print nats.stat.query()
    time.sleep(1)
    nats.unsubscribe(sid)
    nats.stop()

if __name__ == '__main__':
    main()
