class UriInvalidException(Exception):
    def __init__(self, uri):
        self.invalidUri = uri
        self.message = "[{}] {} is invalid!".format(str(self.__class__).split('.')[1], uri)

class NatsException(Exception):
    def __init__(self, desc):
        self.description = "[{}] {}".format(str(self.__class__).split('.')[1], desc)

class NatsServerException(NatsException): pass
class NatsClientException(NatsException): pass
class NatsConnectException(NatsException): pass
class NatsAuthException(NatsException): pass