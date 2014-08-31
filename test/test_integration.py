from fixtures import  NatsServerHelper
import os,sys
import unittest
import tempfile
import shutil

LIB_PATH = os.path.split(os.getcwd())[0]
sys.path.append(LIB_PATH)

from mock import MagicMock, patch

class NatsClientTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        program = cls._get_exe()
        cls.directory = tempfile.mkdtemp(prefix='python-nats')
        cls.processHelper = NatsServerHelper(
            cls.directory,
            proc_name=program)

        cls.processHelper.run(proc_args="-c resources/nats_config.yml")

        addr = "nats://nats:nats@127.0.0.1:4222"
        cls.client = NatsClient().connect_nats({"uri": addr})

    @classmethod
    def tearDownClass(cls):
        cls.processHelper.stop()
        shutil.rmtree(cls.directory)

    @classmethod
    def _is_exe(cls, fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    @classmethod
    def _get_exe(cls):

        PROGRAM = 'nats-server'

        program_path = None
        for path in sys.path:
            path = path.strip('"')
            exe_file = os.path.join(path, PROGRAM)
            if cls._is_exe(exe_file):
                program_path = exe_file
                break

        if not program_path:
            #raise Exception("Nats-Server not in path, skip integration test.")
            sys.exit(0)

        return program_path        

class TestSimple(NatsClientTest):

   def test_publish(self):
       print "skip"


if __name__ == '__main__':
   unittest.main()
