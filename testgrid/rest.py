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
                url = 'http://%s/deploy' % self.host
                data = {}
                list_packages = []
                for pkg in packages:
                        list_packages.append({"name": pkg.name, "version": pkg.version, "type": type(pkg).__name__, "module": type(pkg).__module__})
                data["packages"] = list_packages
                data["session"] = {"username":self.username, "name": self.name}
                headers = {'content-type': 'application/json'}
                r = requests.post(url, data=json.dumps(data), headers=headers)
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
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])

        def allocate_node(self, **opts):
                url = 'http://%s/allocate_node' % self.host
                data = {"session" :{"username":self.username, "name": self.name}}
                data["options"] = opts
                headers = {'content-type': 'application/json'}
                r = requests.post(url, data=json.dumps(data), headers=headers)
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
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])

class Client(testgrid.client.Client):

        def __init__(self, host =  "qa.lab.fr.lan:8080", username = None):
                self.host = host
                self.username = username or getpass.getuser()

        def get_node(self, name):
                url = 'http://%s/get_node?name=%s' % (self.host, name)
                r = requests.get(url)
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

        def is_transient(self, node):pass

        def get_node_session(self, node):
                url = 'http://%s/get_node_session?name=%s' % (self.host, node.name)
                r = requests.get(url)
                data = r.json()
                if "session" in data:
                        return Session(self.host, data["session"]["username"], data["session"]["name"])

        def open_session(self, name = None):
                url = 'http://%s/open_session' % self.host
                data = {}
                data["session"] = {"username": self.username, "name": name}
                headers = {'content-type': 'application/json'}
                r = requests.post(url, data=json.dumps(data), headers=headers)
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])
                return Session(self.host, self.username, name)

        def close_session(self, name):
                url = 'http://%s/close_session' % self.host
                data = {"session" :{"username":self.username, "name": name}}
                headers = {'content-type': 'application/json'}
                r = requests.post(url, data=json.dumps(data), headers=headers)
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])

        def get_session(self, name):
                url = 'http://%s/get_session?name=%s&username=%s' % (self.host, name, self.username)
                r = requests.get(url)
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])
                return Session(self.host, self.username, name)

        def get_sessions(self):
                url = 'http://%s/get_sessions' % self.host
                r = requests.get(url)
                response = r.json()
                sessions = {}
                for session in response["sessions"]:
                        yield Session(self.host, session["username"], session["name"])



        def add_node(self, name, ini):
                url = 'http://%s/add_node' % self.host
                dic = self.get_node_dictionary(name, ini)
                headers = {'content-type': 'application/json'}
                r = requests.post(url, data=json.dumps(dic), headers=headers)
                response = r.json()
                if "error" in response:
                        raise Exception(response["error"])

        def remove_node(self, name):
                url = 'http://%s/remove_node' % self.host

        def quarantine_node(self, name, reason):
                url = 'http://%s/quarantine_node' % self.host

        def rehabilitate_node(self, name):
                url = 'http://%s/rehabilitate_node' % self.host







