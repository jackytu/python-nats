'''
Unit test for nats client
'''
import os, sys, re
import unittest
LIB_PATH = os.path.split(os.getcwd())[0]
sys.path.append(LIB_PATH)

from mock import patch
from nats.common import Common
from nats.protocol import Protocol
from nats.error import NotImplementException

class TestCommon(unittest.TestCase):
    'test common module'
    def test_fake_uri(self):
        'should raise NotImplementedError if parse non string uri'
        self.assertRaises(NotImplementException, 
        	Common.parse_address_info, 123456)

    def test_non_nats_protocol(self):
        'should raise NotImplementedError if parse non nats uri'
        non_nats_uri = 'http://nats:nats@127.0.0.1:4222'
        self.assertRaises(NotImplementException,
        	Common.parse_address_info, non_nats_uri)

    def test_use_default_uri(self):
        'should use default server address if no uri was given'
        user, pswd, host, port = Common.parse_address_info()
        self.assertEqual(user, 'nats')
        self.assertEqual(pswd, 'nats')
        self.assertEqual(host, '127.0.0.1')
        self.assertEqual(port, 4222)

    def test_parse_address_info(self):
        'should return the right value if right uri given'
        nats_uri = 'nats://nats:nats@127.0.0.1:4222'
        user, pswd, host, port = Common.parse_address_info(nats_uri)
        self.assertEqual(user, 'nats')
        self.assertEqual(pswd, 'nats')
        self.assertEqual(host, '127.0.0.1')
        self.assertEqual(port, 4222)

    def test_create_inbox(self):
        'should return random INBOX name'
        inbox1 = Common.create_inbox()
        inbox2 = Common.create_inbox()
        assert '_INBOX' in inbox1
        assert inbox1 != inbox2

class TestProtocol(unittest.TestCase):
    def test_version(self):
        'should return the protocol version' 
        #with patch.dict(Protocol, PROTOCOL_VERSION='0-0-0-0'):
        version = Protocol.version()
        self.assertEqual(version, '0.5.0.beta.12')

    def test_protocol_regular_in_table(self):
        'should return the proto regular if in protocol table'
        with patch.dict(Protocol.PROTOCOL_TABLE, {
           'proto' : 'content'
            }, clear=True):
            self.assertEqual(Protocol.protocol_regular('proto'), 
            	re.compile('content'))
    '''\
    def test_noexist_proto(self):
        'should raise exception if request non-exist protocol'
        with patch.dict(Protocol.PROTOCOL_TABLE, {
           'proto' : 'content'
            }, clear=True):
            self.assertRaises(NotImplementException, 
            	Protocol.protocol_regular, 'noexist')

    '''
    def test_assert_right_proto_type(self):
        'should return True if the msg if matched the reg of  given proto'
        with patch.dict(Protocol.PROTOCOL_TABLE, {
           'proto' : 'content'
            }, clear=True):
            msg = 'content'
            self.assertTrue(Protocol.assert_protocol_type(msg, 'proto'))

    def test_assert_wrong_proto_type(self):
        'should return False if msg not matched the reg of given proto'
        with patch.dict(Protocol.PROTOCOL_TABLE, {
            'proto' : 'content'
              }, clear=True):
            msg = 'somemsg'
            self.assertFalse(Protocol.assert_protocol_type(msg, 'proto'))

    def test_nonexist_proto(self):
        'should return False if proto not in table'
        with patch.dict(Protocol.PROTOCOL_TABLE, {
            'proto' : 'content'
              }, clear=True):
            msg = 'content'
            self.assertFalse(Protocol.assert_protocol_type(msg, 'nonexist'))        

    def test_not_matched(self):
        'should return the un-matched part of message'
        with patch.dict(Protocol.PROTOCOL_TABLE, {
            'proto' : 'content'
              }, clear=True):
            msg = 'content_not_matched'
            self.assertEqual(Protocol.not_matched('proto', msg), '_not_matched')
    def test_matched(self):
        'should return the matched part of message'
        with patch.dict(Protocol.PROTOCOL_TABLE, {
            'proto' : 'content'
              }, clear=True):
            msg = 'content_not_matched'
            self.assertEqual(Protocol.matched('proto', msg), 'content')

    def test_ping_request(self):
        'should return the ping protocol'
        self.assertEqual(Protocol.ping_request(), 'PING\r\n')

    def test_pong_response(self):
        'should return the pong protocol'
        self.assertEqual(Protocol.pong_response(), 'PONG\r\n')

    def test_connect_command(self):
        'should return the connect command'
        opts = {'user' : 'a', 'pass' : 'b'}
        self.assertEqual(Protocol.connect_command(opts), 
         	'CONNECT {"user": "a", "pass": "b"}\r\n')

if __name__ == '__main__':
    unittest.main()
