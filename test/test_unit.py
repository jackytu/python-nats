import os,sys
import unittest

sys.path.insert(0, "/Users/tuzhongying/Tools/homebrew/bin")
sys.path.append("/Users/tuzhongying/Tools/homebrew/lib/python2.7/site-packages")

LIB_PATH = os.path.split(os.getcwd())[0]
sys.path.append(LIB_PATH)

from mock import MagicMock, patch

from nats.client import NatsClient
from nats.error import *

class TestNatsClient(unittest.TestCase):
   def test_server_host_port(self):
        nats = NatsClient()
        proper_addr = "nats://nats:nats@11.12.13.14:4242"
        user, pswd, host, port = nats._server_host_port(proper_addr)
        self.assertEqual(user, "nats")
        self.assertEqual(pswd, "nats")
        self.assertEqual(host, "11.12.13.14")
        self.assertEqual(port, 4242)

        fake_addr = "http://nats:nats@11.12.13.14:4242"
        self.assertRaises(NatsException, nats._server_host_port, fake_addr)

        fake_addr_2 = {"bad": "uri"}
        self.assertRaises(NotImplementedError, nats._server_host_port, fake_addr_2)



if __name__ == '__main__':
    unittest.main()
