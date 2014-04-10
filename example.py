import sys, time
#from nats.client import NatsClient

NATS_URI = "nats://nats:nats@127.0.0.1:4222"

NATS_URI = "nats://nats:nats@127.0.0.1:4222"

sys.path.append("/Users/tuzhongying/Tools/homebrew/lib/python2.7/site-packages")
from nats.client import NatsClient

NATS_URI = "nats://n_user:n_passwd@10.36.166.46:8446"



#NATS_URI = "nats://nats:nats@127.0.0.1:4222"

def main():
    nats = NatsClient(uris=NATS_URI)
    nats.start()
    time.sleep(1)

    def request_blk(msg, reply):
        print  "received {}".format(msg)
        nats.publish(reply, "I can help!")

    def subscribe_blk(msg):
        print "received {}".format(msg)

    def publish_blk():
        print "published one message"

    sid = nats.subscribe("help", request_blk)
    nats.publish("help", "who can help", "", publish_blk)
    nats.request("help", "who can help", subscribe_blk)
    print nats.stat.query()
    time.sleep(1)
    nats.unsubscribe(sid)
    nats.stop()

if __name__ == '__main__':
    main()
