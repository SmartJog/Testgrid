# copyright (c) 2013-2014 smartjog, released under the GPL license.

import testgrid
import getpass
import json
import urllib2

def request_get(url):
        response = urllib2.urlopen(url)
        response.geturl()
        return json.loads(response.read())

def request_post(url, data):
        headers = {'content-type': 'application/json'}
        request = urllib2.Request(url, json.dumps(data), headers)
        response = urllib2.urlopen(request)
        return json.loads(response.read())

class Node(testgrid.model.Node):

        def __init__(self, host ,  name, typename,  hoststring):
                self.name = name
                self.typename = typename
                self.hoststring = hoststring
                self.host = host

        def __eq__(self, other):
                if other.name == self.name:
                        return True
                return False

        def __ne__(self, other):
                return not (self == other)

        def get_typename(self):
                return self.typename

        def get_hoststring(self):
                return testgrid.model.Hoststring(self.hoststring)

        def has_support(self, **opts):
                url = 'http://%s/has_support' % self.host
                data = {"opts": opts, "node": self.name}
                response = request_post(url, data)
                if "error" in response:
                        raise Exception(response["error"])
                return response["result"]

        def get_load(self):pass

        def join(self, subnet):pass

        def leave(self, subnet):pass

        def get_subnets(self):pass

        def get_installed_packages(self):pass

        def is_up(self):
                return 1

        def install(self, package):
                url = 'http://%s/install' % self.host
                data = {"package": {"name": package.name, "version": package.version, "type": type(package).__name__, "module": type(package).__module__}}
                data["node"] =  {"name": self.name}
                response = request_post(url, data)
                if "error" in response:
                        raise Exception(response["error"])
                return response["code"], response["stdout"], response["stderr"]

        def uninstall(self, package):
                url = 'http://%s/uninstall' % self.host
                data = {"package": {"name": package.name, "version": package.version, "type": type(package).__name__, "module": type(package).__module__}}
                data["node"] =  {"name": self.name}
                response = request_post(url, data)
                if "error" in response:
                        raise Exception(response["error"])
                return response["code"], response["stdout"], response["stderr"]


        def is_installed(self, package):
                url = 'http://%s/is_installed' % self.host
                data = {"package": {"name": package.name, "version": package.version, "type": type(package).__name__, "module": type(package).__module__}}
                data["node"] =  {"name": self.name}
                response = request_post(url, data)
                if "error" in response:
                        raise Exception(response["error"])
                return response["result"]

        def is_installable(self, package):
                url = 'http://%s/is_installable' % self.host
                data = {"package": {"name": package.name, "version": package.version, "type": type(package).__name__, "module": type(package).__module__}}
                data["node"] =  {"name": self.name}
                response = request_post(url, data)
                if "error" in response:
                        raise Exception(response["error"])
                return response["result"]


class Session(object):

        def __init__(self, host, username, name = None, user = None):
                self.host = host
                self.username = username
                self.user = user or testgrid.client.get_current_user()
                self.name = name

        def __iter__(self):
                url = 'http://%s/get_nodes_session?name=%s&username=%s' % (self.host, self.name, self.username)
                response = request_get(url)
                if "error" in response:
                        raise Exception(response["error"])
                for node in response["nodes"]:
                        yield Node(self.host, **node)

        def __contains__(self, node):
                url = 'http://%s/session_contains?name=%s&username=%s&node=%s' % (self.host, self.name , self.username, node.name)
                response = request_get(url)
                if "error" in response:
                        raise Exception(response["error"])
                return response["result"]

        def __eq__(self, other):
                if other.name == self.name and other.username == self.username:
                        return True
                return False

        def __ne__(self, other):
                return not (self == other)

        def __len__(self):
                url = 'http://%s/get_nodes_session?name=%s&username=%s' % (self.host, self.name, self.username)
                count = 0
                response = request_get(url)
                if "error" in response:
                        raise Exception(response["error"])
                for node in response["nodes"]:
                        count+= 1
                return count

        def deploy(self, packages):
                url = 'http://%s/deploy' % self.host
                data = {}
                list_packages = []
                for pkg in packages:
                        list_packages.append({"name": pkg.name, "version": pkg.version, "type": type(pkg).__name__, "module": type(pkg).__module__})
                data["packages"] = list_packages
                data["session"] = {"username":self.username, "name": self.name}
                response = request_post(url, data)
                if "error" in response:
                        raise Exception(response["error"])
                plans = []
                for key, value in response.items():
                        plans.append((value["pkg"]["name"] , Node(host = self.host, name = key, **value["args"])))
                return plans

        def undeploy(self):
                url = 'http://%s/undeploy' % self.host
                data = {"session" :{"username":self.username, "name": self.name}}
                response = request_post(url, data)
                if "error" in response:
                        raise Exception(response["error"])

        def allocate_node(self, **opts):
                url = 'http://%s/allocate_node' % self.host
                data = {"session" :{"username":self.username, "name": self.name}}
                data["options"] = opts
                response = request_post(url, data)
                if "error" in response:
                        raise Exception(response["error"])
                return Node(self.host, **response)

        def release(self, node):
                url = 'http://%s/release_node' % self.host
                data = {"session" :{"username":self.username, "name": self.name}}
                data["node"] = {"name": node.name}
                response = request_post(url, data)
                if "error" in response:
                        raise Exception(response["error"])

        def close(self):
                url = 'http://%s/close_session' % self.host
                data = {"session" :{"username":self.username, "name": self.name}}
                response = request_post(url, data)
                if "error" in response:
                        raise Exception(response["error"])

class Client(testgrid.client.Client):

        def __init__(self, host =  "127.0.0.1:8080", username = None):
                self.host = host
                self.username = username or getpass.getuser()

        def get_node(self, name):
                url = 'http://%s/get_node?name=%s' % (self.host, name)
                response = request_get(url)
                if "error" in response:
                        raise Exception(response["error"])
                return Node(self.host, **response)

        def get_nodes(self):
                url = 'http://%s/get_nodes' % self.host
                response = request_get(url)
                for key, value in response.items():
                        yield Node(host = self.host, name = key, **value)

        def is_available(self, node):
                url = 'http://%s/is_available?name=%s' % (self.host, node.name)
                response = request_get(url)
                return response["result"]

        def is_allocated(self, node):
                url = 'http://%s/is_allocated?name=%s' % (self.host, node.name)
                response = request_get(url)
                return response["result"]

        def is_quarantined(self, node):
                url = 'http://%s/is_quarantined?name=%s' % (self.host, node.name)
                response = request_get(url)
                return response["result"]

        def is_transient(self, node):
                url = 'http://%s/is_transient?name=%s' % (self.host, node.name)
                response = request_get(url)
                return response["result"]

        def get_node_session(self, node):
                url = 'http://%s/get_node_session?name=%s' % (self.host, node.name)
                response = request_get(url)
                if "session" in response:
                        return Session(self.host, response["session"]["username"], response["session"]["name"])

        def open_session(self, name = None):
                url = 'http://%s/open_session' % self.host
                data = {}
                data["session"] = {"username": self.username, "name": name}
                response = request_post(url, data)
                if "error" in response:
                        raise Exception(response["error"])
                return Session(self.host, self.username, response["session"]["name"])

        def close_session(self, name):
                url = 'http://%s/close_session' % self.host
                data = {"session" :{"username":self.username, "name": name}}
                response = request_post(url, data)
                if "error" in response:
                        raise Exception(response["error"])

        def get_session(self, name):
                url = 'http://%s/get_session?name=%s&username=%s' % (self.host, name, self.username)
                response = request_get(url)
                if "error" in response:
                        raise Exception(response["error"])
                return Session(self.host, self.username, name)

        def get_sessions(self):
                url = 'http://%s/get_sessions' % self.host
                response = request_get(url)
                for session in response["sessions"]:
                        yield Session(self.host, session["username"], session["name"])

        def add_node(self, name, ini):
                url = 'http://%s/add_node' % self.host
                dic = self.get_node_dictionary(name, ini)
                response = request_post(url, dic)
                if "error" in response:
                        raise Exception(response["error"])

        def remove_node(self, name):
                url = 'http://%s/remove_node?name=%s' % (self.host, name)
                response = request_get(url)
                if "error" in response:
                        raise Exception(response["error"])

        def quarantine_node(self, name, reason):
                url = 'http://%s/quarantine_node' % self.host
                data = {"name": name, "reason": reason}
                response = request_post(url, data)
                if "error" in response:
                        raise Exception(response["error"])

        def rehabilitate_node(self, name):
                url = 'http://%s/rehabilitate_node' % self.host
                data = {"name": name}
                response = request_post(url, data)
                if "error" in response:
                        raise Exception(response["error"])


#########
# tests #
#########

import unittest, controller
import time

class SelfTest(testgrid.client.SelfTest):
        client_cls = Client

	def setUp(self):
		grid = testgrid.model.FakeGenerativeGrid(name = "grid")
		self.server = controller.Server("127.0.0.1", "8080", grid)
		self.server.start()
		time.sleep(1)

	def tearDown(self):
		self.server.terminate()
		self.server.join()

	def test_restricted(self):
		return True

if __name__ == "__main__": unittest.main(verbosity = 2)

