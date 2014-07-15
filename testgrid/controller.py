import bottle
import sys
import testgrid


grid = None
accessmgr = None
app = bottle.Bottle()

class Client(testgrid.client.Client):

    @testgrid.client.restricted
    def add_node(self, **opts):
        node = testgrid.parser.create_node_object(**opts)
        self.grid.add_node(node)
        return node

class AccessManager(testgrid.client.AccessManager):

    def __init__(self, host):
        self.host = host

    def is_administrator(self, user):
        if self.host == user.remote_addr:
            return True
        return False

def setup_serveur(host, port, g, am = None):
    global grid
    global accessmgr
    grid = g
    accessmgr = am or AccessManager(host)
    app.run(host=host, port=port, debug=True)

def setup_client(username):
    user = testgrid.client.User(name = username)
    user.remote_addr = bottle.request.remote_addr
    client = Client(grid = grid, accessmgr = accessmgr , user = user)
    return client


@app.route("/get_node")
def get_node():
    client = setup_client(bottle.request.GET.get("username"))
    name = bottle.request.GET.get("name")
    try:
        node = client.get_node(name)
        return {"name": node.name ,"typename": node.get_info(), "hoststring": node.hoststring}
    except Exception as e:
        return ({"error": "%s" % repr(e)})


@app.route("/get_nodes")
def get_nodes():
    result = {}
    result["nodes"] = []
    client = setup_client(bottle.request.GET.get("username"))
    for node in client.get_nodes():
        result["nodes"].append({"name": node.name, "typename": node.get_info(), "hoststring": node.hoststring})
    return result

@app.route("/is_available")
def is_available():
    name = bottle.request.GET.get("name")
    client = setup_client(bottle.request.GET.get("username"))
    try:
        node = client.get_node(name)
        return ({"result": client.is_available(node)})
    except Exception as e:
        return ({"error": "%s" % repr(e)})

@app.route("/is_allocated")
def is_allocated():
    name = bottle.request.GET.get("name")
    client = setup_client(bottle.request.GET.get("username"))
    try:
        node = client.get_node(name)
        return ({"result": client.is_allocated(node)})
    except Exception as e:
        return ({"error": "%s" % repr(e)})

@app.route("/is_quarantined")
def is_quarantined():
    name = bottle.request.GET.get("name")
    client = setup_client(bottle.request.GET.get("username"))
    try:
        node = client.get_node(name)
        return ({"result": client.is_quarantined(node)})
    except Exception as e:
        return ({"error": "%s" % repr(e)})


@app.route("/is_transient")
def is_transient():
    name = bottle.request.GET.get("name")
    client = setup_client(bottle.request.GET.get("username"))
    try:
        node = client.get_node(name)
        return ({"result": client.is_transient(node)})
    except Exception as e:
        return ({"error": "%s" % repr(e)})

@app.post("/deploy")
def deploy():
    try:
        data = bottle.request.json
        list_packages = []
        for package in data["packages"]:
            cls = testgrid.parser.get_subclass(package["type"],
                                               testgrid.model.Package ,
                                               package["module"])
            list_packages.append(cls(name = package["name"],
                                     version = package["version"]))
        client = setup_client(data["session"]["username"])
        session = client.get_session(data["session"]["name"])
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
        client = setup_client(data["session"]["username"])
        session = client.open_session(data["session"]["name"])
        session.undeploy()
        return {}
    except Exception as e:
        return {"error": repr(e)}

@app.post("/open_session")
def open_session():
    try:
        data = bottle.request.json
        client = setup_client(data["session"]["username"])
        session = client.open_session(data["session"]["name"])
        return {"session" :{"username": session.user.name, "name": session.name}}
    except Exception as e:
        return {"error": repr(e)}

@app.post("/allocate_node")
def allocate_node():
    try:
        data = bottle.request.json
        client = setup_client(data["session"]["username"])
        session = client.open_session(data["session"]["name"])
        node = session.allocate_node(**data["options"])
        return {"name": node.name,"typename": node.get_info(), "hoststring": node.hoststring}
    except Exception as e:
        return {"error": repr(e)}

@app.post("/release_node")
def release_node():
    try:
        data = bottle.request.json
        client = setup_client(data["session"]["username"])
        session = client.get_session(data["session"]["name"])
        node = client.get_node(data["node"]["name"])
        session.release(node)
        return {}
    except Exception as e:
        return {"error": repr(e)}

@app.route('/get_node_session')
def get_node_session():
    name = bottle.request.GET.get("name")
    client = setup_client(bottle.request.GET.get("username"))
    node = client.get_node(name)
    session = client.get_node_session(node)
    if session:
        return {"session": {"username": session.user.name, "name": session.name}}
    return {}

@app.post('/close_session')
def close_session():
    try:
        data = bottle.request.json
        client = setup_client(data["session"]["username"])
        session = client.open_session(data["session"]["name"])
        session.close()
        return {}
    except Exception as e:
        return {"error": repr(e)}

@app.route('/get_sessions')
def get_sessions():
    sessions = {"sessions": []}
    client = setup_client(bottle.request.GET.get("username"))
    for session in client.get_sessions():
        sessions["sessions"].append({"username": session.user.name, "name": session.name})
    return sessions

@app.route('/get_session')
def get_session():
    try:
        name = bottle.request.GET.get("name")
        client = setup_client(bottle.request.GET.get("username"))
        session = client.get_session(name)
        result = {}
        for node in session:
            result[node.name] = {"typename": node.get_info(), "hoststring": node.hoststring}
        return result
    except Exception as e:
        return {"error": repr(e)}

@app.post('/add_node')
def add_node():
    try:
        data = bottle.request.json
        client = setup_client(data["username"])
        client.add_node(**data["node_opt"])
        return {}
    except Exception as e:
        return {"error": repr(e)}

@app.route('/remove_node')
def remove_node():
    try:
        name = bottle.request.GET.get("name")
        client = setup_client(bottle.request.GET.get("username"))
        client.remove_node(name)
        return {}
    except Exception as e:
        return {"error": repr(e)}

@app.post('/quarantine_node')
def quarantine_node():
    try:
        data = bottle.request.json
        client = setup_client(data["username"])
        client.quarantine_node(data["name"], data["reason"])
        return {}
    except Exception as e:
        return {"error": repr(e)}

@app.post('/rehabilitate_node')
def rehabilitate_node():
    try:
        data = bottle.request.json
        client = setup_client(data["username"])
        client.rehabilitate_node(data["name"])
        return {}
    except Exception as e:
         return {"error": repr(e)}

@app.post('/install')
def install():
    try:
        data = bottle.request.json
        client = setup_client(data["username"])
        if node.name == data["node"]["name"]:
            cls = testgrid.parser.get_subclass(data["package"]["type"],
                                               testgrid.model.Package ,
                                               data["package"]["module"])
            code , stdout, stderr = node.install(cls(name = data["package"]["name"], 
                                                     version = data["package"]["version"]))
            return {"code": code, "stdout": stdout, "stderr": stderr}
        return {"error": "node %s doesn't exist" % data["node"]["name"]}
    except Exception as e:
        return {"error": repr(e)}

@app.post('/uninstall')
def uninstall():
    try:
        data = bottle.request.json
        client = setup_client(data["username"])
        node = client.get_node(data["node"]["name"])
        cls = testgrid.parser.get_subclass(data["package"]["type"], testgrid.model.Package , data["package"]["module"])
        code , stdout, stderr = node.uninstall(cls(name = data["package"]["name"], version = data["package"]["version"]))
        return {"code": code, "stdout": stdout, "stderr": stderr}
    except Exception as e:
        return {"error": repr(e)}

@app.post('/is_installed')
def is_installed():
    try:
        data = bottle.request.json
        client = setup_client(data["username"])
        client.get_node(data["node"]["name"])
        cls = testgrid.parser.get_subclass(data["package"]["type"], testgrid.model.Package , data["package"]["module"])
        return {"result": node.is_installed(cls(name = data["package"]["name"], version = data["package"]["version"]))}
    except Exception as e:
        return {"error": repr(e)}

@app.post('/is_installable')
def is_installable():
    try:
        data = bottle.request.json
        client = setup_client(data["username"])
        node = client.get_node(data["node"]["name"])
        cls = testgrid.parser.get_subclass(data["package"]["type"],
                                           testgrid.model.Package ,
                                           data["package"]["module"])
        return {"result":node.is_installable(cls(name = data["package"]["name"], 
                                                 version = data["package"]["version"]))}
    except Exception as e:
        return {"error": repr(e)}

@app.post('/has_support')
def has_support():
    try:
        #FIXME
        data = bottle.request.json
        client = setup_client()
        node = client.get_node(data["node"])
        return {"result": node.has_support(**data["opts"])}
    except Exception as e:
        return {"error": "%s" % repr(e)}

@app.route('/get_nodes_session')
def get_nodes_session():
    name = bottle.request.GET.get("name")
    client = setup_client(bottle.request.GET.get("username"))
    session = client.get_session(name)
    result = {}
    nodes = []
    for node in session:
        nodes.append({"name": node.name ,"typename": node.get_info(), "hoststring": node.hoststring})
    result["nodes"]  = nodes
    return result

@app.route('/session_contains')
def session_contains():
    name = bottle.request.GET.get("name")
    client = setup_client(bottle.request.GET.get("username"))
    session = client.get_session(name)
    node_name = bottle.request.GET.get("node")
    for node in session:
        if node.name == node_name:
            return {"result": True}
    return {"result": False}

import unittest, controller
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

        cls = {
               "generative_grid": testgrid.model.FakeGenerativeGrid, # generative grid
               "package": testgrid.model.FakePackage,
               "subnet": testgrid.model.Subnet,
               "node": testgrid.model.FakeNode,
               "user": testgrid.model.User,
               "grid": testgrid.model.Grid, # non-generative grid
              }

        def setUp(self):
            self.nodes, self.packages, self.grid, self.session = self.mkenv(2, 2)
            self.grid.nodes = list(self.grid.nodes)
            self.server = Server(host = "127.0.0.1", port = "8080", grid = self.grid)
            self.server.start()
            time.sleep(1)

        def tearDown(self):
                self.server.terminate()
                self.server.join()

        def mkenv(self, nb_nodes, nb_packages):
            "create test objects using a non-generative grid"
            nodes = [self.cls["node"]("node%i" % i) for i in xrange(nb_nodes)]
            packages = [self.cls["package"]("pkg%i" % i, "1.0") for i in xrange(nb_packages)]
            subnets = [self.cls["subnet"]("subnet")]
            grid = self.cls["grid"](name = "grid", subnets = subnets, nodes = nodes)
            user = self.cls["user"](name = "user")
            session = grid.open_session(name = "session", user = user)
            return (nodes, packages, grid, session)

        def request_get(self, url):
            return testgrid.rest.request_get(url)

        def request_post(self, url, data):
            return testgrid.rest.request_post(url, data)

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
            self.assertEqual(data, {'nodes': [{'typename': 'fake node', 'hoststring': 'test@test', 'name': 'node0'}, {'typename': 'fake node', 'hoststring': 'test@test', 'name': 'node1'}]})
            data = self.request_get('http://127.0.0.1:8080/remove_node?name=node0')
            self.assertNotIn("error", data)
            data = self.request_get('http://127.0.0.1:8080/get_nodes')
            self.assertEqual(data, {'nodes': [{'typename': 'fake node', 'hoststring': 'test@test', 'name': 'node1'}]})
            self.request_post('http://127.0.0.1:8080/add_node', {"node_opt": {"name": "node", "type": "fake node"}, "username": "user"})
            data = self.request_get('http://127.0.0.1:8080/get_nodes')
            self.assertNotIn("error", data)
            self.assertEqual(data, {'nodes': [{'typename':'fake node','hoststring':'test@test','name':'node1'}, {'typename':'fake node','hoststring':'test@test','name': 'node'}]})

        def test_node_state(self):
            data = self.request_post('http://127.0.0.1:8080/quarantine_node', {"name": "node0", "reason": "test quarantine", "username": "user"})
            self.assertNotIn("error", data)
            data = self.request_get("http://127.0.0.1:8080/is_quarantined?name=node0&username=user")
            self.assertEqual(data, {"result": True})
            data = self.request_post('http://127.0.0.1:8080/rehabilitate_node', {"name": "node0", "username": "user"})
            self.assertNotIn("error", data)
            data = self.request_get("http://127.0.0.1:8080/is_quarantined?name=node0&username=user")
            self.assertEqual(data, {"result": False})

        def test_basic_session_manipulaion(self):
            data = self.request_get("http://127.0.0.1:8080/get_sessions")
            self.assertNotIn("error", data)
            self.assertEqual(data, {'sessions': [{'username': self.session.user.name, 'name':self.session.name}]})
            data = self.request_post("http://127.0.0.1:8080/close_session", {"session" :{"username":self.session.user.name, "name": self.session.name}})
            self.assertNotIn("error", data)
            data = self.request_get("http://127.0.0.1:8080/get_sessions")
            self.assertNotIn("error", data)
            self.assertEqual(data, {'sessions': []})
            data = self.request_post("http://127.0.0.1:8080/open_session", {"session": {"username": "test", "name": "test"}})
            self.assertNotIn("error", data)
            data = self.request_get('http://127.0.0.1:8080/get_sessions')
            self.assertNotIn("error", data)
            self.assertEqual(data, {'sessions': [{'username': 'test', 'name': 'test'}]})

        def test_session_allocate(self):
            data = self.request_get('http://127.0.0.1:8080/is_available?name=node0')
            self.assertEqual(data, {"result": True})
            data = self.request_post("http://127.0.0.1:8080/allocate_node", {"session" :{"username":self.session.user.name, "name": self.session.name}, "options": {}})
            self.assertNotIn("error", data)
            self.assertEqual(data, {'typename':'fake node','hoststring':'test@test', 'name': 'node0'})
            data = self.request_get('http://127.0.0.1:8080/is_available?name=node0')
            self.assertEqual(data, {"result": False})
            data = self.request_post("http://127.0.0.1:8080/allocate_node", {"session" :{"username":self.session.user.name, "name": self.session.name}, "options": {}})
            data = self.request_get('http://127.0.0.1:8080/is_allocated?name=node0')
            self.assertEqual(data, {"result": True})
            data = self.request_get('http://127.0.0.1:8080/session_contains?name=%s&username=%s&node=node0' % (self.session.name, self.session.user.name))
            self.assertEqual(data, {"result": True})
            data = self.request_get('http://127.0.0.1:8080/get_node_session?name=node0')
            self.assertEqual(data, {'session': {'username': self.session.user.name , 'name': self.session.name}})
            data = self.request_post("http://127.0.0.1:8080/allocate_node", {"session" :{"username":self.session.user.name, "name": self.session.name}, "options": {}})
            self.assertIn("error", data)
            data = self.request_get('http://127.0.0.1:8080/get_nodes_session?name=%s&username=%s' % (self.session.name, self.session.user.name))
            self.assertEqual(data, {'nodes': [{'typename': 'fake node', 'hoststring': 'test@test', 'name': 'node0'}, {'typename': 'fake node', 'hoststring': 'test@test', 'name': 'node1'}]})
            data = self.request_post("http://127.0.0.1:8080/release_node", {"session" :{"username":self.session.user.name, "name": self.session.name}, "node": {"name": "node0"}})
            self.assertNotIn("error", data)
            data = self.request_post("http://127.0.0.1:8080/release_node", {"session" :{"username":self.session.user.name, "name": self.session.name}, "node": {"name":"node1"}})
            self.assertNotIn("error", data)
            data = self.request_get('http://127.0.0.1:8080/get_nodes_session?name=%s&username=%s' % (self.session.name, self.session.user.name))
            self.assertEqual(data, {'nodes': []})

        def test_deployment(self):
            list_packages = []
            data =  {}
            for pkg in self.packages:
                list_packages.append({"name": pkg.name, "version": pkg.version, "type": type(pkg).__name__, "module": type(pkg).__module__})
            data["packages"] = list_packages
            data["session"] = {"username":self.session.user.name, "name": self.session.name}
            res = self.request_post("http://127.0.0.1:8080/deploy", data)
            self.assertNotIn("error", res)
            self.assertEqual(res, {'node1': {'args': {'typename': 'fake node', 'hoststring': 'test@test'}, 'pkg': {'version': u'1.0', 'name': 'pkg1'}}, 'node0': {'args': {'typename': 'fake node', 'hoststring': 'test@test'}, 'pkg': {'version': '1.0', 'name': 'pkg0'}}})
            res = self.request_post("http://127.0.0.1:8080/deploy", data)
            self.assertIn("error", res)
            res = self.request_post("http://127.0.0.1:8080/undeploy", {"session" :{"username":self.session.user.name, "name": self.session.name}})
            self.assertNotIn("error", res)
            data = self.request_get('http://127.0.0.1:8080/get_nodes_session?name=%s&username=%s' % (self.session.name, self.session.user.name))
            self.assertEqual(data, {'nodes': []})

#install, uninstall
if __name__ == "__main__": unittest.main(verbosity = 2)
