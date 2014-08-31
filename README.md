[![Build Status](https://travis-ci.org/jackytu/python-nats.png)](https://travis-ci.org/jackytu/python-nats)

# NATS - Python Client

A python client for the [NATS messaging system](https://github.com/derekcollison/nats).

## Installation

```bash
# Python Client
git clone https://github.com/jackytu/python-nats
cd python-nats
python setup install

```

## Basic Usage

```python
import time
from nats.client import NatsClient

nats = NatsClient(uris=NATS_URI)
nats.start()
time.sleep(1)

def request_blk(msg, reply):
    print  "received {}".format(msg)
    nats.publish(reply, "dispatch some job to publishers!")

def subscribe_blk(msg):
    print "received {}".format(msg)

def publish_blk():
    print "callback after published one message"

sid = nats.subscribe("job", subscribe_blk)
nats.publish("job", "I have jobs", "", publish_blk)
nats.request("job", "who has jobs", request_blk)
print nats.stat.query()
time.sleep(1)
nats.unsubscribe(sid)
nats.stop()

```


## License

(The MIT License)

Copyright (c) 2012-2014 Jacky Tu.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
