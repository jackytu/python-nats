import re

class Const:
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
	AWAITING_MSG_PAYLOAD  = 2 #:nodoc:
