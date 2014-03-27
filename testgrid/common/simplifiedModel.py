import getpass
import time


class Node(object):
    def __init__(self, hostname):
        self.hostname = hostname


class Package(object):
    def __init__(self, name, version = None):
        self.name = name
        self.version = version

class responseObject(object):
    def __init__(self, failure, msg, data):
        self.failure = failure
        self.msg = msg
        self.data = data


class Session(object):
    def __init__(self, key=None):
        if not key:
            self.key = "%s@%s" % (getpass.getuser(), time.strftime("%Y%m%d%H%M%S", time.localtime()))
            self.is_anonymous = True
        else:
            self.is_anonymous = False
            self.key = key

    def allocate_node(self, sysname = None, pkg = None):pass

    def release_node(self, node):pass

    def deploy(self, *packages):pass
    
    
    def undeploy(self):pass
