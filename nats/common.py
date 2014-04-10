"common functions"
import urllib, os
from nats.error import (NatsClientException,
	UriInvalidException)

class Common(object):
    'common data'

    ssid = 1

    VERSION = "1.0.0.beta.1"

    DEFAULT_PORT = "4222"
    DEFAULT_URI = "nats://127.0.0.1" + ":" + DEFAULT_PORT

    MAX_RECONNECT_ATTEMPTS = 10
    RECONNECT_TIME_WAIT = 2

    MAX_PENDING_SIZE = 32768

    # Maximum outbound size per client to trigger FP, 20MB
    FAST_PRODUCER_THRESHOLD = (10*1024*1024)

    # Ping intervals
    DEFAULT_PING_INTERVAL = 3
    DEFAULT_PING_MAX = 2


    # Parser
    AWAITING_CONTROL_LINE = 1 #:nodoc:
    AWAITING_MSG_PAYLOAD = 2 #:nodoc:

    @classmethod
    def get_ssid(cls):
        'get the ssid'
        cls.ssid += 1
        return cls.ssid

    @classmethod
    def parse_address_info(cls, server_addr="nats://nats:nats@127.0.0.1:4222"):
        '''\
        parse the metadata nats server uri;

        Params:
        =====
        addr: nats server address;

        Returns:
        =====
        user: username to login nats server;
        pswd: password to login nats server;
        host: ip address of nats server;
        port: port of nats server  
        '''

        if type(server_addr) is not str: 
            raise NatsClientException

        protocol, after_split = urllib.splittype(server_addr)

        if not protocol == "nats": 
            raise UriInvalidException("Invalid uri")
        auth, after_split = urllib.splituser(after_split)
        user_raw, pswd = urllib.splitpasswd(auth)
        user = user_raw.lstrip("/")
        _, after_split = urllib.splithost(after_split)
        host, port = urllib.splitport(after_split)
        return user, pswd, host, int(port)
        
    @classmethod
    def create_inbox(cls):
        '''\
        create a subject that can be used for "directed" communications.
        Returns:
        =====
        inbox name;
        '''
        inbox = ''.join(map(lambda xx:(hex(ord(xx))[2:]), os.urandom(16)))
        return "_INBOX." + inbox

