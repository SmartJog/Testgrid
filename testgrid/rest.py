# copyright (c) 2013-2014 smartjog, released under the GPL license.
import requests
import testgrid
import getpass

class Node(testgrid.model.Node):

        def __init__(self, host ,  name, typename,  hoststring):
                self.name = name
                self.typename = typename
                self.hoststring = hoststring
                self.host = host

        def get_typename(self):
                return self.typename

        def get_hoststring(self):
                return testgrid.model.Hoststring(self.hoststring)

        def has_support(self, **opts):pass

        def get_load(self):pass

        def join(self, subnet):pass

        def leave(self, subnet):pass

        def get_subnets(self):pass

        def get_installed_packages(self):pass

class Session(object):
        def __init__(self, host, username, name = None):
                self.host = host
                self.username = username
                self.name = name

        def deploy(self, packages):
                url = 'http://%s/deploy?' % self.host
                for pkg in packages:
                        url += "pkg=%s=%s+%s&" % (pkg.name, pkg.version, type(pkg).__name__)
                url+= "session=%s+%s" % (self.username, self.name)
                r = requests.get(url)
                data = r.json()
                if "error" in data:
                        raise Exception(data["error"])
                plans = []
                for key, value in data.items():
                        plans.append((value["pkg"], Node(host = self.host, name = key, **value["args"])))
                return plans

        def undeploy(self):
                url = 'http://%s/undeploy?session=%s+%s' % (self.host, self.username, self.name)
                r = requests.get(url)

        def allocate_node(self, **opts):
                url = 'http://%s/allocate_node?'
                for key, value in opts:
                        url += "%s=%s&" % (key, value)
                r = requests.get(url)

        def release_node(node):pass

class Client(testgrid.client.Client):

        def __init__(self, host =  "qa.lab.fr.lan:8080", username = None):
                self.host = host
                self.username = username or getpass.getuser()

        def get_nodes(self):
                url = 'http://%s/get_nodes' % self.host
                r = requests.get(url)
                if r.status_code == 200:
                        data = r.json()
                        for key, value in data.items():
                                yield Node(host = self.host, name = key, **value)
                #return r.raise_for_status()

        def is_available(self, node):
                url = 'http://%s/is_available?name=%s' % (self.host, node.name)
                r = requests.get(url)
                if r.status_code == 200:
                        data = r.json()
                        return data["result"]

        def is_allocated(self, node):
                url = 'http://%s/is_allocated?name=%s' % (self.host, node.name)
                r = requests.get(url)
                if r.status_code == 200:
                        data = r.json()
                        return data["result"]

        def is_quarantined(self, node):
                url = 'http://%s/is_quarantined?name=%s' % (self.host, node.name)
                r = requests.get(url)
                if r.status_code == 200:
                        data = r.json()
                        return data["result"]

        def get_node_session(self, node):
                return None
                #url = 'http://%s/get_node_session?name=%s' % (self.host, node.name)

        def open_session(self, name = None):
                url = 'http://%s/open_session?username=%s&name=%s' % (self.host, self.username, name)
                r = requests.get(url)
                return Session(self.host, self.username, name)
