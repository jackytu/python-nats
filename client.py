#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import os, sys
sys.path.append("/Users/tuzhongying/Tools/homebrew/lib/python2.7/site-packages")

import json
import urllib
import random
import inspect
import time
import copy
from gevent.socket import socket, wait_read, wait_write
from urlparse import urlparse
from const import *
from error import *
import threading 
import gevent
from gevent.queue import  Queue
from gevent.event import AsyncResult
from  threading import Timer
#from conn import NatsConnection
from twisted.internet.task import LoopingCall

class NatsClient():
    """Once connected, send a message, then print the result."""
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

    _DEFAULT_CONN_OPTS = {
        "user": "nats",
        "pass": "nats",
        "verbose" : True,
        "pedantic" : True,
        "ssl_required" : False
    }

    def __init__(self, opts = {}):
        for (k, v) in self._DEFAULT_CLIENT_ATTR.items():
            setattr(self, k, v)

    def connect_nats(self, opts = {}):
        for (k, v) in self._DEFAULT_CONN_OPTS.items():
            if k not in opts:
                self.options[k] = v
            else:
                self.options[k] = opts[k]
        self.options["user"], self.options["pass"], self.host, self.port = \
                                             self._server_host_port(opts["uri"])
        print self.options
        print "hehe in connect_nats"
        self.client, error = self._connect_server(self.host, self.port)
        return self.client, error

    def _connect_server(self, host, port):
        try:
            self.sock = socket()
            client = self.sock.connect((host, port))
            self._on_connection_complete()
            return client, None
        except Exception, e:
            return None, "{}".format(e.message)

    def _setup_data_receiver(self):
        t = threading.Thread(target=self._waiting_data)
        t.setDaemon(True)
        return t

    def _server_host_port(self, addr = DEFAULT_URI):
        if type(addr) is not str: 
            raise NotImplementedError
        try:    
            protocol, s1 = urllib.splittype(addr)
            if not protocol == "nats": 
                raise NatsException("Invalid uri")
            auth, s2 = urllib.splituser(s1)
            u, pswd = urllib.splitpasswd(auth)
            user = u.lstrip("/")
            host_with_port, s3 = urllib.splithost(s2)
            host, port = urllib.splitport(s3)
        except NatsException, e:
            user, pswd, host, port = "nats", "nats", "127.0.0.1", "4001"
        except:
            user, pswd, host, port = "nats", "nats", "127.0.0.1", "4001"
        return user, pswd, host, int(port)

    def _flush_pending(self):
        if not self.pending: return None 
        try: 
            self.sock.sendall("".join(self.pending))
        except Exception, e: 
            self._on_connection_lost(e.message)

        self.pending, self.pending_size = None, 0

    def _on_connection_complete(self):
        self.connected = True
        self.pings_outstanding = 0
        self.pongs_received = 0

        self.data_receiver =  self._setup_data_receiver()
        self.data_receiver.start()

        self.ping_timer = LoopingCall(self._send_ping)
        self.ping_timer.start(self.ping_interval)

    def _on_connection_lost(self, reason):
        self.connected = False
        if self.data_receiver: self.data_receiver.join(1)
        if self.ping_timer: self.ping_timer.cancel()

    def  _waiting_data(self):
        while self.connected:
            try:
                wait_read(self.sock.fileno())
                data = self.sock.recv(1024)
                self._process_data(data)
            except Exception, e:
                self._on_connection_lost(e.message)
                return
    # Returns a subject that can be used for "directed" communications.
    # self.return [String]
    def _create_inbox(self):
        inbox = ''.join(map(lambda xx:(hex(ord(xx))[2:]),os.urandom(16)))
        return "_INBOX." + inbox

    def _send_ping(self):
        self.pings_outstanding += 1
        self._queue_server_rt(self._process_pong)
        self._flush_pending()
        return None

    def _queue_server_rt(self, cb):
        if not cb: return None
        if not self.pongs: self.pongs = Queue()
        self.pongs.put(cb)
        self._send_command(PING_REQUEST)

    def _process_pong(self):
        self.pongs_received += 1
        self.pings_outstanding -= 1

    def _connect_command(self):
        return "CONNECT {}{}".format(json.dumps(self.options), CR_LF)

    def _on_messsage(self, subject, sid, reply, msg):
        # Accounting - We should account for inbound even if they are not processed.
        self.msgs_received += 1
        if msg: self.bytes_received += len(msg)
        if sid not in self.subs: return None
        sub = self.subs[sid]
        # Check for auto_unsubscribe

        sub["received"] += 1
        if sub["max"]:  
            # Client side support in case server did not receive unsubscribe
            if (sub["received"] > sub["max"]): return self.unsubscribe(sid) 
            # cleanup here if we have hit the max..
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

        # Check for a timeout, and cancel if received >= expected
        if (sub["timeout"] and sub["received"] >= sub["expected"]):
             sub["timeout"].cancel()

        def timer_proc():
            if auto_unsubscribe: self.unsubscribe(sid) 
            if callback: callback(sid) 
        sub["timeout"] = Timer(timeout, timer_proc)

        self.subs[sid] = sub

    def _process_info(self, info):
        self.server_info = json.loads(info)
        if self.server_info["auth_required"]:
            self._send_connect_command()
        return self.server_info

    def _send_connect_command(self):
        self._send_command(self._connect_command(), True)

    def _send_command(self, command, priority = False):
        if not self.pending : self.pending = []
        if not priority: self.pending.append(command)
        if priority: self.pending.insert(0, command) 
        self.pending_size += len(command)
        self._flush_pending()
        return True

    def _process_data(self,data):
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
                        # If we are here we do not have a complete line yet that we understand.
                        return None
                    if (self.buf and len(self.buf) == 0 ) : self.buf = []
            if self.parse_state == AWAITING_MSG_PAYLOAD:
                    if not (self.needed and len(self.buf) >= (self.needed + CR_LF_SIZE)): return None 
                    self._on_messsage(self.sub, self.sid, self.reply, self.buf[0:self.needed])
                    self.buf = self.buf[(self.needed + CR_LF_SIZE):len(self.buf)]
                    self.sub = self.sid = self.reply = self.needed = None
                    self.parse_state = AWAITING_CONTROL_LINE
                    if (self.buf and len(self.buf) ==0 ): self.buf = None


   # Publish a message to a given subject, with optional reply subject and completion block
    # self.param [String] subject
    # self.param [Object, #to_s] msg
    # self.param [String] opt_reply
    # self.param [Block] blk, closure called when publish has been processed by the server.
    def publish(self, subject, msg=EMPTY_MSG, opt_reply="", blk=None):
        #self._ensure_client()
        if not subject: return None
        msg = str(msg)
        self.msgs_sent += 1
        self.bytes_sent += len(msg)

        self._send_command("PUB {} {} {}{}{}{}".format(subject, opt_reply, len(msg), 
                                                                           CR_LF,  msg,  CR_LF))
        if blk: self._queue_server_rt(blk)

    # Subscribe to a subject with optional wildcards.
    # Messages will be delivered to the supplied callback.
    # Callback can take any number of the supplied arguments as defined by the list: msg, reply, sub.
    # Returns subscription id which can be passed to #unsubscribe.
    # self.param [String] subject, optionally with wilcards.
    # self.param [Hash] opts, optional options hash, e.g. :queue, :max.
    # self.param [Block] callback, called when a message is delivered.
    # self.return [Object] sid, Subject Identifier
    def subscribe(self, subject, opts={}, callback=None):
        #TODO: NEED DECORATOR
        #self._ensure_client()
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

   # Cancel a subscription.
    # self.param [Object] sid
    # self.param [Number] opt_max, optional number of responses to receive before auto-unsubscribing
    def unsubscribe(self, sid, opt_max=None):
        #self._ensure_client()
        opt_max_str = ""
        if opt_max: opt_max_str = " " + str(opt_max)
        self._send_command("UNSUB {}{}{}".format(sid, opt_max_str, CR_LF))
        if not sid in  self.subs: return None
        sub = self.subs[sid]
        sub["max"] = opt_max
        if not (sub["max"] and (sub["received"] < sub["max"])): 
            del(self.subs[sid]) 

    # Return the active subscription count.
    # self.return [Number]
    def subscription_count(self):
        return len(self.subs)

    def timeout(self, sid, timeout, opts={}, callback=None):
        #self._ensure_client()
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

    # Send a request and have the response delivered to the supplied callback.
    # self.param [String] subject
    # self.param [Object] msg
    # self.param [Block] callback
    # self.return [Object] sid
    def request(self, subject, data=None, opts={}, cb=None):
        #self._ensure_client()
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

# this connects the protocol to a server runing on port 8000
def main():
    nats = NatsClient()
    conn, error  = nats.connect_nats({
        "uri" : "nats://nats:nats@127.0.0.1:4242"}
    )
    i = 2
    while i>1:
        time.sleep(1)
        i -= 1
        def callback_sub(msg, reply):
            nats.publish(reply, "reply for this")
            print  "received {}".format(msg)
        def callback_pub():
            print "publish msg"

        sid = nats.subscribe("python-nats", {}, callback_sub)
        nats.publish("python-nats", "hello-world", "", callback_pub)
        nats.request("python-nats", "hello-world", {}, callback_pub)
        #nats.unsubscribe(sid)
    
# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()
