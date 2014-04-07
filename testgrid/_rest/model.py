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

    
