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

nats = NatsClient()
conn, error  = nats.connect_nats({
    "uri" : NATS_URI })

if error: sys.exit(-1)

time.sleep(1)

def request_cb(msg, reply):
    print  "received {}".format(msg)
    nats.publish(reply, "I can help!")

def subscribe_cb(msg):
    print "received {}".format(msg)

def publish_cb():
    print "published one message"

sid = nats.subscribe("help", {}, request_cb)
nats.publish("help", "who can help", "", publish_cb)
nats.request("help", "who can help", {}, subscribe_cb)
time.sleep(1)
nats.unsubscribe(sid)

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
