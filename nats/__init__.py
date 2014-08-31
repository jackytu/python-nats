'''\
[Basic Knowledge]
      Python version client of NATS message bus, through this client library, 
      devs could publish, subscribe, request with timeout, reponse numbers 
      options.

      Publish: advertise a message with topic in NATS protocol, the NATS se-
      rver will diliver this message to all subscribers intrested in this topic;

      Subscribe: subscribe topics from NATS server, if message of these top-
      ics was published, the subsciber would receive them;

[Usage]
    #initialize a nats client 
    nats = NatsClient(uris=NATS_URI)
    nats.start()

    #subscribe a topic , and do something if received message;
    def subscribe_blk(msg):
        print "received {}".format(msg)
    sid = nats.subscribe("help", subscribe_blk)
  
    #publish a message with a topic, do something if finished.
    def publish_blk():
        print "published one message"
     nats.publish("help", "who can help", "", publish_blk)

    #publish a message with topic, and reply to the publishers;
    def request_blk(msg, reply):
        print  "received {}".format(msg)
        nats.publish(reply, "this job is for you.")
    nats.request("help", "who can do this job", request_blk)

    #Get current statistics of client
    print nats.stat.query()

    #Unsubscribe some topic
    nats.unsubscribe(sid)

    #stop a nats client
    nats.stop()

'''

__title__ = 'nats'
__version__ = '0.1.0.beta.1'
__licence__ = 'MIT'
__copyright__ = 'Copyright 2014, Jacky Tu under MIT licence, v0.1.0.beta.1'

from nats.client import NatsClient
from nats.common import Common
from nats.protocol import Protocol
from nats.stat import Stat

__all__ = ['NatsClient', 'Common', 'Protocol', 'Stat']
