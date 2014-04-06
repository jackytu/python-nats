#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import os, sys
import json, urllib, random
import inspect, time, copy
import threading, gevent, urlparse
from gevent.socket import ( 
             socket, wait_read, wait_write)

from const import *
from error import *
from threading import Timer
from gevent.queue import  Queue
from gevent.event import AsyncResult
from twisted.internet.task import LoopingCall

class NatsClient():
    #default nats client attributes
    _DEFAULT_CLIENT_ATTR = {
       "ssid" : 1,
       "subs" : {},
       "options" : {},
       "connected" : False,
       "msgs_received" : 0,
       "msgs_sent" : 0,
       "bytes_received" : 0,
       "bytes_sent" : 0,
       "needed" : 0,
       "pending" : [],
       "pings" : 0,
       "pongs" : 0,
       "ping_timer" : None,
       "pings_outstanding" : 0,
       "pongs_received" : 0, 
       "ping_interval" : DEFAULT_PING_INTERVAL,
       "max_outstanding_pings" : DEFAULT_PING_MAX,
       "pending_size" : 0,
       "parse_state" : AWAITING_CONTROL_LINE,
       "buf" : None,
       "sock" : None,
       "cient" : None,
       "data_receiver" : None
    }

    #default nats connection options.
    _DEFAULT_CONN_OPTS = {
        "user": "nats",
        "pass": "nats",
        "verbose" : True,
        "pedantic" : True,
        "ssl_required" : False
    }

    def __init__(self):
        for (k, v) in self._DEFAULT_CLIENT_ATTR.items():
            setattr(self, k, v)

    def _connect_server(self, host, port):
        """
        connect to nats server;

        Params:
        =====
        host: nats server ip address;
        port: nats server listen port;

        Returns:
        =====
        client: nats connection;
        error: error destription if exists;
        """
        try:
            """Use default gevent socket paramters : 
            family = AF_INET
            type = SOCKE_STREAM
            protocol = auto detect
            """
            self.sock = socket()
            self.sock.settimeout(3)
            client = self.sock.connect((host, port))
            self._on_connected()
            return client, None
        except Exception, e:
            return None, "{}".format(e.message)

    def _setup_data_receiver(self):
        """
        setup daemon thread waiting for data from nats server.

        Params:
        =====
        None

        Returns:
        =====
        t: daemon thread

        """

        t = threading.Thread(target=self._waiting_data)
        t.setDaemon(True)
        return t

    def _server_host_port(self, addr = DEFAULT_URI):
        """
        parse the metadata nats server uri;

        Params:
        =====
        addr: nats server address, use "nats://127.0.0.1:4242" if not given;

        Returns:
        =====
        user: username to login nats server;
        pswd: password to login nats server;
        host: ip address of nats server;
        port: port of nats server

        """
        if type(addr) is not str: 
            raise NotImplementedError
        protocol, s1 = urllib.splittype(addr)
        if not protocol == "nats": 
            raise NatsException("Invalid uri")
        auth, s2 = urllib.splituser(s1)
        u, pswd = urllib.splitpasswd(auth)
        user = u.lstrip("/")
        host_with_port, s3 = urllib.splithost(s2)
        host, port = urllib.splitport(s3)

        return user, pswd, host, int(port)

    def _flush_pending(self):
        "flush pending data of current connection."

        if not self.pending: return None 
        try: 
            self.sock.sendall("".join(self.pending))
        except Exception, e: 
            self._on_connection_lost(e.message)

        self.pending, self.pending_size = None, 0

    def _on_connected(self):
        """
        actions when connect to nats server, actions as below:
        1. setup a ping timer for detect the connectivity of connection;
        2. setup a data receiver for listening the socket;
        """

        self.connected = True
        self.pings_outstanding = 0
        self.pongs_received = 0

        self.data_receiver =  self._setup_data_receiver()
        self.data_receiver.start()

        self.ping_timer = LoopingCall(self._send_ping)
        self.ping_timer.start(self.ping_interval)

    def _on_connection_lost(self, reason):
        """
        action if connection losted, actions including:
        1. cancel data receiver; (@2014-04-06)
        2. cancel ping timer; (@2014-04-06)
        3. reconnect; (TODO）
        """

        self.connected = False
        if self.data_receiver: self.data_receiver.join(1)
        if self.ping_timer: self.ping_timer.cancel()
        raise NatsException("Connection losted.")

    def  _waiting_data(self):
        """
        waiting for data from nats server
        """

        while self.connected:
            try:
                wait_read(self.sock.fileno())
                data = self.sock.recv(1024)
                self._process_data(data)
            except Exception, e:
                self._on_connection_lost(e.message)
                return

    def _create_inbox(self):
        """
        create a subject that can be used for "directed" communications.
        Returns:
        =====
        inbox name;
        """
        inbox = ''.join(map(lambda xx:(hex(ord(xx))[2:]),os.urandom(16)))
        return "_INBOX." + inbox

    def _send_ping(self):
        "send ping request to nats server"

        self.pings_outstanding += 1
        self._queue_server_rt(self._process_pong)
        self._flush_pending()

    def _queue_server_rt(self, cb):
        "handshake with nats server by ping-pong"

        if not cb: return None
        if not self.pongs: self.pongs = Queue()
        self.pongs.put(cb)
        self._send_command(PING_REQUEST)

    def _process_pong(self):
        "process pong response from nats server"

        self.pongs_received += 1
        self.pings_outstanding -= 1

    def _connect_command(self):
        "connect protocol"

        return "CONNECT {}{}".format(json.dumps(self.options), CR_LF)

    def _on_messsage(self, subject, sid, msg, reply = None):
        """
        actions when received messages from nats server;

        Params:
        =====
        subject: message subject;
        sid: subscriber id;
        reply: inbox name if exists
        msg: message body

        """

        self.msgs_received += 1
        if msg: self.bytes_received += len(msg)
        if sid not in self.subs: return None
        sub = self.subs[sid]

        #unsubscribe subscriber if received enough messages; 
        sub["received"] += 1
        if sub["max"]:  
            if (sub["received"] > sub["max"]): return self.unsubscribe(sid) 
            if (sub["received"] == sub["max"]): del(self.subs[sid])

        callback  = sub["callback"]
        if callback:
            args, varargs, keywords, defaults = inspect.getargspec(callback)
            args_len = len(args)
            if args_len == 0: 
                callback()
            elif args_len == 1:
                callback(msg)
            elif args_len == 2:
                callback(msg, reply)
            else:
                callback.call(msg, reply, subject)

        # cancel autounscribe timer, if subscriber request with timeout, 
        # and receive enough messages;
        if (sub["timeout"] and sub["received"] >= sub["expected"]):
             sub["timeout"].cancel()

        def timer_proc():
            if auto_unsubscribe: self.unsubscribe(sid) 
            if callback: callback(sid) 

        sub["timeout"] = Timer(timeout, timer_proc)

        self.subs[sid] = sub

    def _process_info(self, info):
        """
        process server infomation message;
        
        Params:
        =====
        info: nats server information 

        """
        self.server_info = json.loads(info)
        if self.server_info["auth_required"]:
            self._send_connect_command()

    def _send_connect_command(self):
        "send connect command to nats server"

        self._send_command(self._connect_command(), True)

    def _send_command(self, command, priority = False):
        """
        send command to nats server;
        
        Params:
        =====
        command: the command string;
        priority: command priority;

        """
        if not self.pending : self.pending = []
        if not priority: self.pending.append(command)
        if priority: self.pending.insert(0, command) 
        self.pending_size += len(command)
        self._flush_pending()

    def _process_data(self,data):
        "process data received from nats server, disptch data to proper handles"

        if not data: return
        if not self.buf: 
            self.buf = data
        else:
            self.buf += data
        while (self.buf):
            if self.parse_state == AWAITING_CONTROL_LINE:
                    if MSG.match(self.buf):
                        self.buf = re.split(MSG, self.buf)[2:]
                        parse_list = MSG.findall(self.buf)
                        self.sub, self.sid, self.reply, self.needed = parse_list[0], \
                                    int(parse_list[1]), parse_list[3], int(parse_list[4])
                        self.parse_state = AWAITING_MSG_PAYLOAD
                        
                    elif OK.match(self.buf): 
                        self.buf = re.split(OK, self.buf)[2:]
                    elif ERR.match(self.buf):
                        self.buf = re.split(OK, self.buf)[2:]
                    elif PING.match(self.buf):
                        self.pings += 1
                        self.buf =  "".join(re.split(OK, self.buf)[2:])
                        self._send_command(PONG_RESPONSE)
                    elif PONG.match(self.buf):
                        self.buf =  ''.join(re.split(OK, self.buf)[2:])
                        cb = self.pongs.get()
                        if cb: cb()
                    elif INFO.match(self.buf):
                        parse_list = INFO.findall(self.buf)
                        self.buf =  "".join(re.split(OK, self.buf)[2:])
                        self._process_info(parse_list[0])
                    elif UNKNOWN.match(self.buf):
                        self.buf =  re.split(OK, self.buf)[2:]
                        print "Unknwn protocol"
                    else:
                        return None
                    if (self.buf and len(self.buf) == 0 ) : self.buf = []
            if self.parse_state == AWAITING_MSG_PAYLOAD:
                    if not (self.needed and len(self.buf) >= (self.needed + CR_LF_SIZE)): 
                        return None 
                    self._on_messsage(self.sub, self.sid, self.buf[0:self.needed], self.reply)
                    self.buf = self.buf[(self.needed + CR_LF_SIZE):len(self.buf)]
                    self.sub = self.sid = self.reply = self.needed = None
                    self.parse_state = AWAITING_CONTROL_LINE
                    if (self.buf and len(self.buf) ==0 ): self.buf = None


    def connect_nats(self, opts = {}):
        """
        connect to nats server

        Params: 
        =====
        opts: connect options;

        Returns:
        =====
        client: nats connection;
        error: error description if exists any;
        """

        for (k, v) in self._DEFAULT_CONN_OPTS.items():
            if k not in opts:
                self.options[k] = v
            else:
                self.options[k] = opts[k]
        self.options["user"], self.options["pass"], self.host, self.port = \
                                             self._server_host_port(opts["uri"])
        self.client, error = self._connect_server(self.host, self.port)
        return self.client, error


    def publish(self, subject, msg=EMPTY_MSG, opt_reply="", blk=None):
        """
        Publish a message to a given subject, with optional reply subject and 
        completion block

        Params:
        =====
        subject: message subject;
        msg: message body;
        opt_reply: reply inbox if needs;
        blk: closure called when publish has been processed by the server.     

        """
        if not subject: return None
        msg = str(msg)
        self.msgs_sent += 1
        self.bytes_sent += len(msg)

        self._send_command("PUB {} {} {}{}{}{}".format(subject, opt_reply, len(msg), 
                                                                           CR_LF,  msg,  CR_LF))
        if blk: self._queue_server_rt(blk)

    def subscribe(self, subject, opts={}, callback=None):
        """
        Subscribe to a subject with optional wildcards.
        Messages will be delivered to the supplied callback.
        Callback can take any number of the supplied arguments as defined by the 
        list: msg, reply, sub.

        Params:
        =====
        subject: optionally with wilcards.
        opts:  optional options hash, e.g. "queue", "max".
        callback, called when a message is delivered.

        Returns:
        =====
        sid: Subject Identifier
        Returns subscription id which can be passed to #unsubscribe.
        """

        if not subject: return None
        self.ssid += 1
        sid = self.ssid
        q = ""

        sub = { "subject" : subject, "received" : 0 }
        sub["callback"] = callback

        if "queue" in opts: 
            q = sub["queue"] = opts["queue"]
 
        if "max" in opts: sub["max"] = opts["max"] 

        self._send_command("SUB {} {} {}{}".format(subject, q, 
                                                                       sid, CR_LF))
        self.subs[sid] = sub

        # Setup server support for auto-unsubscribe
        if "max" in opts: self.unsubscribe(sid, opts["max"])
        return sid


    def unsubscribe(self, sid, opt_max=None):
        """
        Cancel a subscription.

        Params:
        =====
        sid: Subject Identifier
        opt_max: optional number of responses to receive before auto-unsubscribing.      
        """
        opt_max_str = ""
        if opt_max: opt_max_str = " " + str(opt_max)
        self._send_command("UNSUB {}{}{}".format(sid, opt_max_str, CR_LF))
        if not sid in  self.subs: return None
        sub = self.subs[sid]
        sub["max"] = opt_max
        if not (sub["max"] and (sub["received"] < sub["max"])): 
            del(self.subs[sid]) 

    def timeout(self, sid, timeout, opts={}, callback=None):
        """
        Setup a timeout for receiving messages for the subscription.

        Params:
        =====
        sid: Subject Identifier
        timeout: integer in seconds
        opts: options, :auto_unsubscribe(true), :expected(1)
        """

        if not sid in self.subs: return None
        sub = self.subs[sid]
        auto_unsubscribe, expected = True, 1

        if  "auto_unsubscribe" in opts:
            auto_unsubscribe = opts["auto_unsubscribe"]

        if "expected" in opts:
            expected = opts["expected"]

        def pblock():
            if auto_unsubscribe: self.unsubscribe(sid)
            if callback: callback(sid)

        sub["timeout"] = Timer(timeout, pblock)
        sub["expected"] = expected
        self.subs[sid] = sub

    def request(self, subject, data=None, opts={}, cb=None):
        """
        Send a request and have the response delivered to the supplied callback.

        Params:
        =====
        subject: message subject;
        msg: message payload;
        callback: callback if any;

        Returns:
        =====
        sid: Subject Identifier
        """

        if not subject: return None
        inbox = self._create_inbox()
        def process_reply(msg, reply):
            args, varargs, keywords, defaults = inspect.getargspec(cb)
            args_len = len(args)
            if args_len == 0: 
                cb()
            elif args_len == 1:
                cb(msg)
            else:
                cb(msg, reply)

        s = self.subscribe(inbox, opts, process_reply)
        self.publish(subject, data, inbox)
        return s

