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
from nats.client import NatsClient

def callback_sub(msg, reply):
    nats.publish(reply, "reply for this")
    print  "received {}".format(msg)
def callback_pub():
    print "publish msg"

sid = nats.subscribe("python-nats", {}, callback_sub)
nats.publish("python-nats", "hello-world", "", callback_pub)
nats.request("python-nats", "hello-world", {}, callback_pub)

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
