import time
import sys

from nats.client import NatsClient

NATS_URI = "nats://nats:nats@127.0.0.1:4222"

def main():
    try:
        nats = NatsClient(uris=NATS_URI)
        nats.start()
        time.sleep(1)

        print nats.stat.query()

        def request_blk(msg):
            print "[SUB]: {}".format(msg)
            print nats.stat.query()
            nats.stop()

        def subscribe_blk(msg, reply):
            print "[PUB]: {}".format(msg)
            nats.publish(reply, "I can do this job.")

        sid = nats.subscribe("job", subscribe_blk)
        nats.request("job", "who can do this job?", request_blk)
        print nats.stat.query()
    except KeyboardInterrupt, ex:
        print "ByeBye."
        sys.exit(0)

if __name__ == '__main__':
    main()
