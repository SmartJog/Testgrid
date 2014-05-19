import bottle
import sys
import testgrid


grid = None
app = bottle.Bottle()

def setup_serveur(host, port, g):
    global grid
    grid = g
    app.run(host=host, port=port, debug=True)

def get_session(username, name):
    for session in grid.get_sessions():
        if (session.username == username and session.name == name):
            return session
    raise Exception("session %s %s doesn't exist" % (username, name))

@app.route("/get_node")
def get_node():
    name = bottle.request.GET.get("name")
    for node in grid:
        if node.name == name:
            return {"name": node.name ,"typename": node.get_typename(), "hoststring": node.hoststring}
    return ({"error": "node %s doesn' exist" % name})

@app.route("/get_nodes")
def get_nodes():
    result = {}
    for node in grid:
        result[node.name] = {"typename": node.get_typename(), "hoststring": node.hoststring}
    return result

@app.route("/is_available")
def is_available():
    name = bottle.request.GET.get("name")
    for node in grid:
        if name == node.name:
            return ({"result": grid.is_available(node)})
    return ({"error": "node %s doesn' exist" % name})

@app.route("/is_allocated")
def is_allocated():
    name = bottle.request.GET.get("name")
    for node in grid:
        if name == node.name:
            return ({"result": grid.is_allocated(node)})
    return ({"error": "node %s doesn' exist" % name})

@app.route("/is_quarantined")
def is_quarantined():
    name = bottle.request.GET.get("name")
    for node in grid:
        if name == node.name:
            return ({"result": grid.is_quarantined(node)})
    return ({"error": "node %s doesn' exist" % name})

@app.route("/is_transient")
def is_transient():
    name = bottle.request.GET.get("name")
    for node in grid:
        if name == node.name:
            return ({"result": grid.is_transient(node)})
    return ({"error": "node %s doesn' exist" % name})

@app.post("/deploy")
def deploy():
    try:
        data = bottle.request.json
        list_packages = []
        for package in data["packages"]:
            cls = testgrid.parser.get_subclass(package["type"], testgrid.model.Package ,package["module"])
            list_packages.append(cls(name = package["name"], version = package["version"]))
        session = get_session(data["session"]["username"], data["session"]["name"])
        plans = session.deploy(list_packages)
        result = {}
        for pkg, node in plans:
            result[node.name] = {"pkg":{"name": pkg.name, "version": pkg.version}, "args": {"typename": node.get_typename(), "hoststring": node.hoststring}}
        return result
    except Exception as e:
        return {"error": repr(e)}

@app.post("/undeploy")
def undeploy():
    try:
        data = bottle.request.json
        session = get_session(data["session"]["username"], data["session"]["name"])
        session.undeploy()
        return {}
    except Exception as e:
        return {"error": repr(e)}

@app.post("/open_session")
def open_session():
    try:
        data = bottle.request.json
        session = grid.open_session(data["session"]["username"], data["session"]["name"])
        return {"session" :{"username": session.username, "name": session.name}}
    except Exception as e:
        return {"error": repr(e)}

@app.post("/allocate_node")
def allocate_node():
    try:
        data = bottle.request.json
        session = get_session(data["session"]["username"], data["session"]["name"])
        node = session.allocate_node(**data["options"])
        return {"name": node.name,"typename": node.get_typename(), "hoststring": node.hoststring}
    except Exception as e:
        return {"error": repr(e)}

@app.post("/release_node")
def release_node():
    try:
        data = bottle.request.json
        session = get_session(data["session"]["username"], data["session"]["name"])
        for node in grid:
            if node.name == data["node"]["name"]:
                session.release_node(node)
                return {}
        return ({"error": "node %s doesn' exist" % data["node"]["name"]})
    except Exception as e:
        return {"error": repr(e)}

@app.route('/get_node_session')
def get_node_session():
    name = bottle.request.GET.get("name")
    for session in grid.get_sessions():
        for node in session:
            if node.name == name:
                return {"session": {"username": session.username, "name": session.name}}
    return {}

@app.post('/close_session')
def close_session():
    try:
        data = bottle.request.json
        session = get_session(data["session"]["username"], data["session"]["name"])
        session.close()
        return {}
    except Exception as e:
        return {"error": repr(e)}

@app.route('/get_sessions')
def get_sessions():
    sessions = {"sessions": []}
    for session in grid.get_sessions():
        sessions["sessions"].append({"username": session.username, "name": session.name})
    return sessions

@app.route('/get_session')
def get_session_rest():
    try:
        name = bottle.request.GET.get("name")
        uername = bottle.request.GET.get("username")
        session = get_session(username, name)
        result = {}
        for node in session:
            result[node.name] = {"typename": node.get_typename(), "hoststring": node.hoststring}
        return result
    except Exception as e:
        return {"error": repr(e)}

@app.post('/add_node')
def add_node():
    try:
        data = bottle.request.json
        if "type" in data:
            cls = testgrid.parser.get_subclass(testgrid.parser.normalized(data["type"]), testgrid.model.Node)
            del data["type"]
            node = testgrid.parser.Parser._mkobj(cls, **data)
            grid.add_node(node)
            return {}
        else:
            raise Exception("node type wasn't provided")
    except Exception as e:
        return {"error": repr(e)}

@app.route('/remove_node')
def remove_node():
    try:
        name = bottle.request.GET.get("name")
        for node in grid:
            if node.name == name:
                grid.remove_node(node)
                return {}
        return {"error": "can't remove node %s doesn't exist" % name}
    except Exception as e:
        return {"error": repr(e)}

@app.post('/quarantine_node')
def quarantine_node():
    try:
        data = bottle.request.json
        for node in grid:
            if node.name == data["name"]:
                grid.quarantine_node(node, data["reason"])
                return {}
        return {"error": "can't quarantine node %s doesn't exist" % name}
    except Exception as e:
        return {"error": repr(e)}

@app.post('/rehabilitate_node')
def rehabilitate_node():
    try:
        data = bottle.request.json
        for node in grid:
            if node.name == data["name"]:
                grid.rehabilitate_node(node)
                return {}
        return {"error": "can't rehabilitate node %s doesn't exist" % name}
    except Exception as e:
        return {"error": repr(e)}

@app.post('/install')
def install():
    try:
        data = bottle.request.json
        for node in grid:
            if node.name == data["node"]["name"]:
                cls = testgrid.parser.get_subclass(data["package"]["type"], testgrid.model.Package , data["package"]["module"])
                code , stdout, stderr = node.install(cls(name = data["package"]["name"], version = data["package"]["version"]))
                return {"code": code, "stdout": stdout, "stderr": stderr}
        return {"error": "node %s doesn't exist" % data["node"]["name"]}
    except Exception as e:
        return {"error": repr(e)}

@app.post('/uninstall')
def uninstall():
    try:
        data = bottle.request.json
        for node in grid:
            if node.name == data["node"]["name"]:
                cls = testgrid.parser.get_subclass(data["package"]["type"], testgrid.model.Package , data["package"]["module"])
                code , stdout, stderr = node.uninstall(cls(name = data["package"]["name"], version = data["package"]["version"]))
                return {"code": code, "stdout": stdout, "stderr": stderr}
        return {"error": "node %s doesn't exist" % data["node"]["name"]}
    except Exception as e:
        return {"error": repr(e)}

@app.post('/is_installed')
def is_installed():
    try:
        data = bottle.request.json
        for node in grid:
            if node.name == data["node"]["name"]:
                cls = testgrid.parser.get_subclass(data["package"]["type"], testgrid.model.Package , data["package"]["module"])
                return {"result": node.is_installed(cls(name = data["package"]["name"], version = data["package"]["version"]))}
        return {"error": "node %s doesn't exist" % data["node"]["name"]}
    except Exception as e:
        return {"error": repr(e)}

@app.post('/is_installable')
def is_installable():
    try:
        data = bottle.request.json
        for node in grid:
            if node.name == data["node"]["name"]:
                cls = testgrid.parser.get_subclass(data["package"]["type"], testgrid.model.Package , data["package"]["module"])
                return {"result":node.is_installable(cls(name = data["package"]["name"], version = data["package"]["version"]))}
        return {"error": "node %s doesn't exist" % data["node"]["name"]}
    except Exception as e:
        return {"error": repr(e)}

@app.route('/get_nodes_session')
def get_nodes_session():
    name = bottle.request.GET.get("name")
    username = bottle.request.GET.get("username")
    session = get_session(username, name)
    result = {}
    nodes = []
    for node in session:
        nodes.append({"name": node.name ,"typename": node.get_typename(), "hoststring": node.hoststring})
    result["nodes"]  = nodes
    return result

@app.route('/session_contains')
def session_contains():
    name = bottle.request.GET.get("name")
    username = bottle.request.GET.get("username")
    session = get_session(username, name)
    node_name = bottle.request.GET.get("node")
    for node in session:
        if node.name == node_name:
            return {"result": True}
    return {"result": False}

import unittest, controller
import sys
import multiprocessing
import json, urllib2
import time

class Server(multiprocessing.Process):

        def __init__(self, host, port, grid):
            super(Server, self).__init__()
            self.host = host
            self.port = port
            self.grid = grid

        def run(self):
                controller.setup_serveur(self.host , self.port, self.grid)

class SelfTest(unittest.TestCase):

        def setUp(self):
            self.nodes, self.packages, self.grid, self.session = testgrid.model.SelfTest.mkenv(2, 2)
            self.server = Server(host = "127.0.0.1", port = "8080", grid = self.grid)
            self.server.start()
            time.sleep(1)

        def tearDown(self):
                self.server.terminate()
                self.server.join()

        def request_get(self, url):
            response = urllib2.urlopen(url)
            response.geturl()
            return json.loads(response.read())

        def request_post(self, url, data):
            headers = {'content-type': 'application/json'}
            request = urllib2.Request(url, json.dumps(data), headers)
            response = urllib2.urlopen(request)
            return json.loads(response.read())

        def test_basic_node_manipulation(self):
            data = self.request_get('http://127.0.0.1:8080/get_node?name=fake')
            self.assertIn("error", data)
            data = self.request_get('http://127.0.0.1:8080/get_node?name=node0')
            self.assertEqual(data, {'typename': 'fake node', 'hoststring': 'test@test', 'name': 'node0'})
            data = self.request_get('http://127.0.0.1:8080/is_available?name=node0')
            self.assertEqual(data, {"result": True})
            data = self.request_get('http://127.0.0.1:8080/is_allocated?name=node0')
            self.assertEqual(data, {"result": False})
            data = self.request_get('http://127.0.0.1:8080/is_quarantined?name=node0')
            self.assertEqual(data, {"result": False})
            data = self.request_get('http://127.0.0.1:8080/is_transient?name=node0')
            self.assertEqual(data, {"result": False})

        def test_add_remove_node(self):
            data = self.request_get('http://127.0.0.1:8080/get_nodes')
            self.assertNotIn("error", data)
            self.assertEqual(len(data), 2)
            self.assertIn("node0", data)
            self.assertIn("node1", data)
            self.assertEqual(data["node0"], {'typename': 'fake node', 'hoststring': u'test@test'})
            data = self.request_get('http://127.0.0.1:8080/remove_node?name=node0')
            self.assertNotIn("error", data)
            data = self.request_get('http://127.0.0.1:8080/get_nodes')
            self.assertEqual(data, {'node1': {'typename': 'fake node', 'hoststring': 'test@test'}})
            self.request_post('http://127.0.0.1:8080/add_node', {"name": "node", "type": "fake node"})
            data = self.request_get('http://127.0.0.1:8080/get_nodes')
            self.assertNotIn("error", data)
            self.assertEqual(data, {'node1': {'typename':'fake node','hoststring':'test@test'},'node': {'typename':'fake node','hoststring':'test@test'}})

        def test_node_state(self):
            data = self.request_post('http://127.0.0.1:8080/quarantine_node', {"name": "node0", "reason": "test quarantine"})
            self.assertNotIn("error", data)
            data = self.request_get("http://127.0.0.1:8080/is_quarantined?name=node0")
            self.assertEqual(data, {"result": True})
            data = self.request_post('http://127.0.0.1:8080/rehabilitate_node', {"name": "node0"})
            self.assertNotIn("error", data)
            data = self.request_get("http://127.0.0.1:8080/is_quarantined?name=node0")
            self.assertEqual(data, {"result": False})

        def test_basic_session_manipulaion(self):
            data = self.request_get("http://127.0.0.1:8080/get_sessions")
            self.assertNotIn("error", data)
            self.assertEqual(data, {'sessions': [{'username': self.session.username, 'name':self.session.name}]})
            data = self.request_post("http://127.0.0.1:8080/close_session", {"session" :{"username":self.session.username, "name": self.session.name}})
            self.assertNotIn("error", data)
            data = self.request_get("http://127.0.0.1:8080/get_sessions")
            self.assertNotIn("error", data)
            self.assertEqual(data, {'sessions': []})
            data = self.request_post("http://127.0.0.1:8080/open_session", {"session": {"username": "test", "name": "test"}})
            self.assertNotIn("error", data)

        def test_session(self):pass

        def test_session_allocate(self):
            data = self.request_get('http://127.0.0.1:8080/is_available?name=node0')
            self.assertEqual(data, {"result": True})
            data = self.request_post("http://127.0.0.1:8080/allocate_node", {"session" :{"username":self.session.username, "name": self.session.name}, "options": {}})
            self.assertNotIn("error", data)
            self.assertEqual(data, {'typename':'fake node','hoststring':'test@test', 'name': 'node0'})
            data = self.request_get('http://127.0.0.1:8080/is_available?name=node0')
            self.assertEqual(data, {"result": False})
            data = self.request_post("http://127.0.0.1:8080/allocate_node", {"session" :{"username":self.session.username, "name": self.session.name}, "options": {}})
            data = self.request_get('http://127.0.0.1:8080/is_allocated?name=node0')
            self.assertEqual(data, {"result": True})
            data = self.request_post("http://127.0.0.1:8080/allocate_node", {"session" :{"username":self.session.username, "name": self.session.name}, "options": {}})
            self.assertEqual(data, {'error': 'NodePoolExhaustedError()'})
            data = self.request_get('http://127.0.0.1:8080/get_nodes_session?name=%s&username=%s' % (self.session.name, self.session.username))
            self.assertEqual(data, {'nodes': [{'typename': 'fake node', 'hoststring': 'test@test', 'name': 'node0'}, {'typename': 'fake node', 'hoststring': 'test@test', 'name': 'node1'}]})
            data = self.request_post("http://127.0.0.1:8080/release_node", {"session" :{"username":self.session.username, "name": self.session.name}, "node": {"name": "node0"}})
            self.assertNotIn("error", data)
            data = self.request_post("http://127.0.0.1:8080/release_node", {"session" :{"username":self.session.username, "name": self.session.name}, "node": {"name":"node1"}})
            self.assertNotIn("error", data)
            data = self.request_get('http://127.0.0.1:8080/get_nodes_session?name=%s&username=%s' % (self.session.name, self.session.username))
            self.assertEqual(data, {'nodes': []})

        def test_deployment(self):
            list_packages = []
            data =  {}
            for pkg in self.packages:
                list_packages.append({"name": pkg.name, "version": pkg.version, "type": type(pkg).__name__, "module": type(pkg).__module__})
            data["packages"] = list_packages
            data["session"] = {"username":self.session.username, "name": self.session.name}
            res = self.request_post("http://127.0.0.1:8080/deploy", data)
            self.assertNotIn("error", res)
            self.assertEqual(res, {'node1': {'args': {'typename': 'fake node', 'hoststring': 'test@test'}, 'pkg': {'version': u'1.0', 'name': 'pkg1'}}, 'node0': {'args': {'typename': 'fake node', 'hoststring': 'test@test'}, 'pkg': {'version': '1.0', 'name': 'pkg0'}}})
            res = self.request_post("http://127.0.0.1:8080/deploy", data)
            self.assertEqual(res, {'error': 'NodePoolExhaustedError()'})
            res = self.request_post("http://127.0.0.1:8080/undeploy", {"session" :{"username":self.session.username, "name": self.session.name}})
            self.assertNotIn("error", res)
            data = self.request_get('http://127.0.0.1:8080/get_nodes_session?name=%s&username=%s' % (self.session.name, self.session.username))
            self.assertEqual(data, {'nodes': []})

#install, uninstall
if __name__ == "__main__": unittest.main(verbosity = 2)
