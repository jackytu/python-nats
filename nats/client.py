# -*- coding: iso-8859-1 -*-
import os, sys
import json, urllib, random
import inspect, time, weakref
import threading, gevent, urlparse
from gevent.socket import ( 
                         socket, wait_read)

from const import *
from error import *
from nats.stat import Stat
from nats.common import Common
from nats.heartbeat import Heartbeat
from nats.connector import Connector
from nats.protocol import Protocol
from threading import Timer
from gevent.queue import  Queue

class NatsClient(object):
    'nats client'

    def __init__(self, **argvs):
        self.subs = {}
        self.buf = None
        self.parse_state = Common.AWAITING_CONTROL_LINE
        self.stat = Stat()
        self.conn = Connector(callback=self.process_data, **argvs)

        print self.conn
        self.ping_timer = Heartbeat(self.conn)

        print self.__str__()  

    def start(self):
        'start nats client'
        self.conn.open()
        self.ping_timer.start()

    def stop(self):
        'start nats client'
        self.conn.close()
        self.ping_timer.cancel()

    def _on_messsage(self, subject, sid, msg, reply=None):
        '''\
        actions when received messages from nats server;

        Params:
        =====
        subject: message subject;
        sid: subscriber id;
        reply: inbox name if exists
        msg: message body
        '''
        self.stat.msgs_received += 1
        if msg: 
            self.stat.bytes_received += len(msg)

        if sid not in self.subs: 
            return
        sub = self.subs[sid]

        #unsubscribe subscriber if received enough messages; 
        sub["received"] += 1
        if "max" in sub:  
            if sub["received"] > sub["max"]: 
                return self.unsubscribe(sid) 
            if sub["received"] == sub["max"]: 
                del self.subs[sid]

        callback = sub["callback"]

        if callback:
            args, _, _, _ = inspect.getargspec(callback)
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
        if "timeout" in sub  \
                    and sub["timeout"] \
                    and sub["received"] >= sub["expected"]:
            sub["timeout"].cancel()
            sub["timeout"] = None

        self.subs[sid] = sub

    def _process_info(self, info):
        '''\
        process server infomation message;
        
        Params:
        =====
        info: nats server information 
        '''
        server_info = json.loads(info)
        print 'process info'
        if server_info["auth_required"]:
            conn_opts = self.conn.get_connection_options()
            self.conn.send_command(Protocol.connect_command(conn_opts), 
                True)

    def publish(self, subject, msg=Protocol.EMPTY_MSG, opt_reply="", blk=None):
        '''\
        Publish a message to a given subject, with optional reply subject and 
        completion block

        Params:
        =====
        subject: message subject;
        msg: message body;
        opt_reply: reply inbox if needs;
        blk: closure called when publish has been processed by the server.     

        '''
        if not self.conn.connected: 
            raise NatsClientException("Connection losted")
        if not subject: 
            return None
        msg = str(msg)

        self.stat.msgs_sent += 1
        self.stat.bytes_sent += len(msg)

        self.conn.send_command("PUB {} {} {}{}{}{}".format(subject, 
            opt_reply, len(msg), Protocol.CR_LF, msg, Protocol.CR_LF))
        if blk: 
            self.ping_timer.queue_server_rt(blk)

    def subscribe(self, subject, callback=None, **opts):
        '''\
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
        '''

        print self.conn.connected

        if not self.conn.connected: 
            raise NatsClientException("Connection losted")
        if not subject: 
            return None
        sid = Common.get_ssid()
        queue_str = ""
        sub = {"subject" : subject, "received" : 0}
        sub["callback"] = callback
        if "queue" in opts: 
            queue_str = sub["queue"] = opts["queue"]
        if "max" in opts: 
            sub["max"] = opts["max"] 
        self.conn.send_command("SUB {} {} {}{}".format(subject, queue_str, 
            sid, Protocol.CR_LF))
        self.subs[sid] = sub
        # Setup server support for auto-unsubscribe
        if "max" in opts: 
            self.unsubscribe(sid, opts["max"])
        return sid

    def unsubscribe(self, sid, opt_max=None):
        '''\
        Cancel a subscription.

        Params:
        =====
        sid: Subject Identifier
        opt_max: optional number of responses to receive 
        before auto-unsubscribing.      
        '''
        if not self.conn.connected: 
            raise NatsClientException("Connection losted")
        opt_max_str = ""
        if opt_max: 
            opt_max_str = " " + str(opt_max)
        self.conn.send_command("UNSUB {}{}{}".format(sid, 
            opt_max_str, Protocol.CR_LF))
        if not sid in  self.subs: 
            return None
        sub = self.subs[sid]
        sub["max"] = opt_max
        if not (sub["max"] and (sub["received"] < sub["max"])): 
            del self.subs[sid]

    def timeout(self, sid, timeout, callback=None, **opts):
        '''\
        Setup a timeout for receiving messages for the subscription.

        Params:
        =====
        sid: Subject Identifier
        timeout: integer in seconds
        opts: options, :auto_unsubscribe(true), :expected(1)
        '''
        if not self.conn.connected: 
            raise NatsClientException("Connection losted")
        if not sid in self.subs: 
            return None
        sub = self.subs[sid]
        auto_unsubscribe, expected = True, 1

        if  "auto_unsubscribe" in opts:
            auto_unsubscribe = opts["auto_unsubscribe"]

        if "expected" in opts:
            expected = opts["expected"]

        def pblock():
            'closure block for timeout request'
            if auto_unsubscribe: 
                self.unsubscribe(sid)
            if callback: 
                callback(sid)

        sub["timeout"] = Timer(timeout, pblock)
        sub["timeout"].start()
        sub["expected"] = expected
        self.subs[sid] = sub

    def request(self, subject, data=None, blk=None, **opts):
        '''\
        Send a request and have the response delivered to the supplied callback.

        Params:
        =====
        subject: message subject;
        msg: message payload;
        callback: callback if any;

        Returns:
        =====
        sid: Subject Identifier
        '''
        if not self.conn.connected: 
            raise NatsClientException("Connection losted")
        if not subject: 
            return None
        inbox = Common.create_inbox()
        def process_reply(msg, reply):
            'closure block of request'
            args, _, _, _ = inspect.getargspec(blk)
            args_len = len(args)
            if args_len == 0: 
                blk()
            elif args_len == 1:
                blk(msg)
            else:
                blk(msg, reply)

        sid = self.subscribe(inbox, process_reply, **opts)
        self.publish(subject, data, inbox)
        return sid

    def process_data(self, data):
        "process data received from nats server, disptch data to proper handles"

        if not data: 
            return
        if not self.buf:
            self.buf = data
        else:
            self.buf += data
        print "received {}".format(data)

        assert_protocol_type = Protocol.assert_protocol_type
        not_matched = Protocol.not_matched
        matched = Protocol.matched

        while self.buf:
            print "buf.{}".format(self.buf)
            if self.parse_state == Common.AWAITING_CONTROL_LINE:
                if assert_protocol_type(self.buf, 'msg'):
                    print "matched message"
                    sub, sid, _, reply, needed = matched('msg', self.buf)
                    self.buf = not_matched('msg', self.buf)
                    sid = int(sid)
                    needed = int(needed)                     
                    self.parse_state = Common.AWAITING_MSG_PAYLOAD
                elif assert_protocol_type(self.buf, 'ok'): 
                    self.buf = not_matched('ok', self.buf)
                    print "parseed ok"
                elif assert_protocol_type(self.buf, 'err'):
                    self.buf = not_matched('err', self.buf)
                    print "Nats server error."  
                elif assert_protocol_type(self.buf, 'ping'):
                    self.ping_timer.on_ping_request()
                    self.buf = not_matched('ping', self.buf)
                elif assert_protocol_type(self.buf, 'pong'):
                    self.buf = not_matched('pong', self.buf)
                    self.ping_timer.on_pong_response()
                elif assert_protocol_type(self.buf, 'info'):
                    self._process_info(matched('info', self.buf))
                    self.buf = not_matched('info', self.buf)
                elif assert_protocol_type(self.buf, 'unknown'):
                    self.buf = not_matched('ok', self.buf)
                    raise NatsException("Unknown protocol")
                else:
                    return None
                if self.buf and len(self.buf) == 0: 
                    self.buf = None
            if self.parse_state == Common.AWAITING_MSG_PAYLOAD:
                if not (needed and 
                    len(self.buf) >= (needed + Protocol.CR_LF_SIZE)): 
                    return None 
                self._on_messsage(sub, sid, self.buf[0 : needed], reply)
                cr_lf_size = Protocol.CR_LF_SIZE

                self.buf = self.buf[(needed + cr_lf_size) : len(self.buf)]
                sub = sid = reply = needed = None
                self.parse_state = Common.AWAITING_CONTROL_LINE
                if self.buf and len(self.buf) == 0: 
                    self.buf = None

    def __str__(self):
        return "python-nats-{}".format(Common.VERSION)


