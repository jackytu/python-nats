'''\
Class Protocol:
     - protocol of NATS;

'''
import re, json

class Protocol(object):
    "nats protocol class"

    CR_LF = "\r\n" 
    CR_LF_SIZE = len(CR_LF)
    EMPTY_MSG = '' 

    PROTOCOL_VERSION = '0.5.0.beta.12'
    
    PROTOCOL_TABLE = {
        "msg" : r"\AMSG\s+([^\s]+)\s+([^\s]+)\s+(([^\s]+)[^\S\r\n]+)?(\d+)\r\n",
        "ok" : r"\A\+OK\s*\r\n",
        "err" : r"\A-ERR\s+('.+')?\r\n",
        "ping" : r"\APING\s*\r\n",
        "pong" : r"\APONG\s*\r\n",
        "info" : r"\AINFO\s+([^\r\n]+)\r\n",
        "unknown" : r"\A(.*)\r\n"
     }    
 
    @classmethod
    def version(cls):
        'acquire the nats protocol version'
        return cls.PROTOCOL_VERSION

    @classmethod
    def protocol_regular(cls, proto):
        'acquire the protocol regular expession'
        exp = cls.PROTOCOL_TABLE.get(proto)
        if not exp:
            raise NotImplementedError
        return re.compile(exp)

    @classmethod
    def assert_protocol_type(cls, msg, proto):
        'check if the protocol type'
        if proto not in cls.PROTOCOL_TABLE: 
            return False
        if cls.protocol_regular(proto).match(msg):
            return True
        else:
            return False

    @classmethod
    def not_matched(cls, proto, msg):
        'return the not matched part of msg'
        reg = cls.protocol_regular(proto)
        return re.split(reg, msg)[-1]

    @classmethod
    def matched(cls, proto, msg):
        'return the matched data'
        reg = cls.protocol_regular(proto)
        return re.findall(reg, msg)[0]

    @classmethod
    def ping_request(cls):
        'ping request to nats server'
        return "PING" + cls.CR_LF 

    @classmethod
    def pong_response(cls):
        'pong response from nats server'
        return "PONG" + cls.CR_LF 

    @classmethod
    def connect_command(cls, conn_opts):
        'connect command to nats server'
        return "CONNECT {}{}".format(json.dumps(conn_opts), cls.CR_LF)
