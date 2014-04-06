import re

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

# Protocol
# self.private
MSG      = re.compile("\AMSG\s+([^\s]+)\s+([^\s]+)\s+(([^\s]+)[^\S\r\n]+)?(\d+)\r\n", re.IGNORECASE) #:nodoc:
OK       = re.compile("\A\+OK\s*\r\n", re.IGNORECASE) #:nodoc:
ERR      = re.compile("\A-ERR\s+('.+')?\r\n", re.IGNORECASE) #:nodoc:
PING     = re.compile("\APING\s*\r\n", re.IGNORECASE) #:nodoc:
PONG     = re.compile("\APONG\s*\r\n" , re.IGNORECASE) #:nodoc:
INFO     = re.compile("\AINFO\s+([^\r\n]+)\r\n", re.IGNORECASE) #:nodoc:
UNKNOWN  = re.compile("\A(.*)\r\n")  #:nodoc:

# Responses
CR_LF = "\r\n" #:nodoc:
CR_LF_SIZE = len(CR_LF)#:nodoc:

PING_REQUEST  = "PING" + CR_LF #:nodoc:
PONG_RESPONSE = "PONG" + CR_LF #:nodoc:

EMPTY_MSG = '' #:nodoc:

# Used for future pedantic Mode
SUB = re.compile("^([^\.\*>\s]+|>$|\*)(\.([^\.\*>\s]+|>$|\*))*$") #:nodoc:
SUB_NO_WC = re.compile("^([^\.\*>\s]+)(\.([^\.\*>\s]+))*$") #:nodoc:

# Parser
AWAITING_CONTROL_LINE = 1 #:nodoc:
AWAITING_MSG_PAYLOAD  = 2 #:nodoc:

# Autostart properties
AUTOSTART_PID_FILE = "/tmp/nats-server.pid"
AUTOSTART_LOG_FILE = "/tmp/nats-server.log"
