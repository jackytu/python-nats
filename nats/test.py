class Common(object):
    ssid = 0

    @classmethod
    def get_id(cls):
        cls.ssid += 1
        return cls.ssid

def func2(p, a='a', b=None, **args ):
     print p
     print a
     print b
     print args

def func(**args):
     func2(a='a', **args)
     print args

if __name__ == '__main__':
    #print Common.get_id()
    #print Common.get_id()
    func2(1, c='c')


