# copyright (c) 2013-2014 smartjog, released under the GPL license.

import requests
import testgrid
import getpass
import json

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

        def has_support(self, **opts):pass

        def get_load(self):pass

        def join(self, subnet):pass

        def leave(self, subnet):pass

        def get_subnets(self):pass

        def get_installed_packages(self):pass

        def install(self, package):
                url = 'http://%s/install' % self.host
                data = {"package": {"name": package.name, "version": package.version, "type": type(package).__name__, "module": type(package).__module__}}
                data["node"] =  {"name": self.name}
                headers = {'content-type': 'application/json'}
                r = requests.post(url, data=json.dumps(data), headers=headers)
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])
                return response["code"], response["stdout"], response["stderr"]

        def uninstall(self, package):
                url = 'http://%s/uninstall' % self.host
                data = {"package": {"name": package.name, "version": package.version, "type": type(package).__name__, "module": type(package).__module__}}
                data["node"] =  {"name": self.name}
                headers = {'content-type': 'application/json'}
                r = requests.post(url, data=json.dumps(data), headers=headers)
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])
                return response["code"], response["stdout"], response["stderr"]


        def is_installed(self, package):
                url = 'http://%s/is_installed' % self.host
                data = {"package": {"name": package.name, "version": package.version, "type": type(package).__name__, "module": type(package).__module__}}
                data["node"] =  {"name": self.name}
                headers = {'content-type': 'application/json'}
                r = requests.post(url, data=json.dumps(data), headers=headers)
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])
                return response["result"]

        def is_installable(self, package):
                url = 'http://%s/is_installable' % self.host
                data = {"package": {"name": package.name, "version": package.version, "type": type(package).__name__, "module": type(package).__module__}}
                data["node"] =  {"name": self.name}
                headers = {'content-type': 'application/json'}
                r = requests.post(url, data=json.dumps(data), headers=headers)
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])
                return response["result"]


class Session(object):

        def __init__(self, host, username, name = None):
                self.host = host
                self.username = username
                self.name = name

        def __iter__(self):
                url = 'http://%s/get_nodes_session?name=%s&username=%s' % (self.host, self.name, self.username)
                r = requests.get(url)
                r.raise_for_status()
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])
                for node in response["nodes"]:
                        yield Node(self.host, **node)

        def __contains__(self, node):
                url = 'http://%s/session_contains?name=%s&username=%s&node=%s' % (self.host, self.name , self.username, node.name)
                r = requests.get(url)
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])
                return response["result"]

        def __eq__(self, other):
                if other.name == self.name and other.username == self.username:
                        return True
                return False

        def __ne__(self, other):
                return not (self == other)

        def deploy(self, packages):
                url = 'http://%s/deploy' % self.host
                data = {}
                list_packages = []
                for pkg in packages:
                        list_packages.append({"name": pkg.name, "version": pkg.version, "type": type(pkg).__name__, "module": type(pkg).__module__})
                data["packages"] = list_packages
                data["session"] = {"username":self.username, "name": self.name}
                headers = {'content-type': 'application/json'}
                r = requests.post(url, data=json.dumps(data), headers=headers)
                r.raise_for_status()
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])
                plans = []
                for key, value in response.items():
                        plans.append((value["pkg"]["name"] , Node(host = self.host, name = key, **value["args"])))
                return plans

        def undeploy(self):
                url = 'http://%s/undeploy' % self.host
                data = {"session" :{"username":self.username, "name": self.name}}
                headers = {'content-type': 'application/json'}
                r = requests.post(url, data=json.dumps(data), headers=headers)
                r.raise_for_status()
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])

        def allocate_node(self, **opts):
                url = 'http://%s/allocate_node' % self.host
                data = {"session" :{"username":self.username, "name": self.name}}
                data["options"] = opts
                headers = {'content-type': 'application/json'}
                r = requests.post(url, data=json.dumps(data), headers=headers)
                r.raise_for_status()
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])
                return Node(self.host, **response)

        def release_node(self, node):
                url = 'http://%s/release_node' % self.host
                data = {"session" :{"username":self.username, "name": self.name}}
                data["node"] = {"name": node.name}
                headers = {'content-type': 'application/json'}
                r = requests.post(url, data=json.dumps(data), headers=headers)
                r.raise_for_status()
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])

        def close(self):
                url = 'http://%s/close_session' % self.host
                data = {"session" :{"username":self.username, "name": self.name}}
                headers = {'content-type': 'application/json'}
                r = requests.post(url, data=json.dumps(data), headers=headers)
                r.raise_for_status()
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])

class Client(testgrid.client.Client):

        def __init__(self, host =  "127.0.0.1:8080", username = None):
                self.host = host
                self.username = username or getpass.getuser()

        def get_node(self, name):
                url = 'http://%s/get_node?name=%s' % (self.host, name)
                r = requests.get(url)
                r.raise_for_status()
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])
                return Node(self.host, **response)

        def get_nodes(self):
                url = 'http://%s/get_nodes' % self.host
                r = requests.get(url)
                r.raise_for_status()
                data = r.json()
                for key, value in data.items():
                        yield Node(host = self.host, name = key, **value)

        def is_available(self, node):
                url = 'http://%s/is_available?name=%s' % (self.host, node.name)
                r = requests.get(url)
                r.raise_for_status()
                data = r.json()
                return data["result"]

        def is_allocated(self, node):
                url = 'http://%s/is_allocated?name=%s' % (self.host, node.name)
                r = requests.get(url)
                r.raise_for_status()
                data = r.json()
                return data["result"]

        def is_quarantined(self, node):
                url = 'http://%s/is_quarantined?name=%s' % (self.host, node.name)
                r = requests.get(url)
                r.raise_for_status()
                data = r.json()
                return data["result"]

        def is_transient(self, node):
                url = 'http://%s/is_transient?name=%s' % (self.host, node.name)
                r = requests.get(url)
                r.raise_for_status()
                data = r.json()
                return data["result"]

        def get_node_session(self, node):
                url = 'http://%s/get_node_session?name=%s' % (self.host, node.name)
                r = requests.get(url)
                r.raise_for_status()
                data = r.json()
                if "session" in data:
                        return Session(self.host, data["session"]["username"], data["session"]["name"])

        def open_session(self, name = None):
                url = 'http://%s/open_session' % self.host
                data = {}
                data["session"] = {"username": self.username, "name": name}
                headers = {'content-type': 'application/json'}
                r = requests.post(url, data=json.dumps(data), headers=headers)
                r.raise_for_status()
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])
                return Session(self.host, self.username, response["session"]["name"])

        def close_session(self, name):
                url = 'http://%s/close_session' % self.host
                data = {"session" :{"username":self.username, "name": name}}
                headers = {'content-type': 'application/json'}
                r = requests.post(url, data=json.dumps(data), headers=headers)
                r.raise_for_status()
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])

        def get_session(self, name):
                url = 'http://%s/get_session?name=%s&username=%s' % (self.host, name, self.username)
                r = requests.get(url)
                r.raise_for_status()
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])
                return Session(self.host, self.username, name)

        def get_sessions(self):
                url = 'http://%s/get_sessions' % self.host
                r = requests.get(url)
                r.raise_for_status()
                response = r.json()
                sessions = {}
                for session in response["sessions"]:
                        yield Session(self.host, session["username"], session["name"])

        def add_node(self, name, ini):
                url = 'http://%s/add_node' % self.host
                dic = self.get_node_dictionary(name, ini)
                headers = {'content-type': 'application/json'}
                r = requests.post(url, data=json.dumps(dic), headers=headers)
                r.raise_for_status()
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])

        def remove_node(self, name):
                url = 'http://%s/remove_node?name=%s' % (self.host, name)
                r = requests.get(url)
                r.raise_for_status()
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])

        def quarantine_node(self, name, reason):
                url = 'http://%s/quarantine_node' % self.host
                data = {"name": name, "reason": reason}
                headers = {'content-type': 'application/json'}
                r = requests.post(url, data=json.dumps(data), headers=headers)
                r.raise_for_status()
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])

        def rehabilitate_node(self, name):
                url = 'http://%s/rehabilitate_node' % self.host
                data = {"name": name}
                headers = {'content-type': 'application/json'}
                r = requests.post(url, data=json.dumps(data), headers=headers)
                r.raise_for_status()
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])


import unittest, controller
import sys
import multiprocessing


class Server(multiprocessing.Process):
        def run(self):
                grid = testgrid.model.FakeGrid(name = "grid")
                controller.setup_serveur("127.0.0.1", "8080", grid)

class SelfTest(testgrid.client.SelfTest):
        client_cls = Client

        def setUp(self):
                self.server = Server()
                self.server.start()
                time.sleep(3)

        def tearDown(self):
                self.server.terminate()
                self.server.join()

if __name__ == "__main__": unittest.main(verbosity = 2)

