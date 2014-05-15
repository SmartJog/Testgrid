"""
Usage:
  my_program --host NAME --port NAME --grid NAME --manifest INI

Options:
  -g NAME, --grid NAME       set grid section NAME in the manifest [default: grid]
  --host NAME                ...
  --port NAME                ...
  -m INI, --manifest INI     comma-separated list of .ini filepaths or URIs [default: ~/grid.ini]

"""
import docopt
import bottle
from bottle import route, request, Bottle, abort
import sys
import testgrid

app = Bottle()
grid = None

def get_session(username, name):
    for session in grid.get_sessions():
        if (session.username == username and session.name == name):
            return session
    raise Exception("session %s %s doesn't exist" % (username, name))

@app.route("/get_node")
def get_node():
    name = request.GET.get("name")
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
    name = request.GET.get("name")
    for node in grid:
        if name == node.name:
            return ({"result": grid.is_available(node)})
    return ({"error": "node %s doesn' exist" % name})

@app.route("/is_allocated")
def is_allocated():
    name = request.GET.get("name")
    for node in grid:
        if name == node.name:
            return ({"result": grid.is_allocated(node)})
    return ({"error": "node %s doesn' exist" % name})

@app.route("/is_quarantined")
def is_quarantined():
    name = request.GET.get("name")
    for node in grid:
        if name == node.name:
            return ({"result": grid.is_quarantined(node)})
    return ({"error": "node %s doesn' exist" % name})

@app.route("/is_transient")
def is_transient():
    name = request.GET.get("name")
    for node in grid:
        if name == node.name:
            return ({"result": grid.is_transient(node)})
    return ({"error": "node %s doesn' exist" % name})

@app.post("/deploy")
def deploy():
    try:
        data = request.json
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
        data = request.json
        session = get_session(data["session"]["username"], data["session"]["name"])
        session.undeploy()
        return {}
    except Exception as e:
        return {"error": repr(e)}

@app.post("/open_session")
def open_session():
    try:
        data = request.json
        session = grid.open_session(data["session"]["username"], data["session"]["name"])
        return {}
    except Exception as e:
        return {"error": repr(e)}

@app.post("/allocate_node")
def allocate_node():
    try:
        data = request.json
        session = get_session(data["session"]["username"], data["session"]["name"])
        node = session.allocate_node(**data["options"])
        return {"name": node.name,"typename": node.get_typename(), "hoststring": node.hoststring}
    except Exception as e:
        return {"error": repr(e)}

@app.post("/release_node")
def release_node():
    try:
        data = request.json
        session = get_session(data["session"]["username"], data["session"]["name"])
        for node in grid:
            print data["node"]["name"], node.name
            if node.name == data["node"]["name"]:
                session.release_node(node)
                print session.plan
                return {}
        return ({"error": "node %s doesn' exist" % data["node"]["name"]})
    except Exception as e:
        return {"error": repr(e)}

@app.route('/get_node_session')
def get_node_session():
    name = request.GET.get("name")
    for session in grid.get_sessions():
        for node in session:
            if node.name == name:
                return {"session": {"username": session.username, "name": session.name}}
    return {}

@app.post('/close_session')
def close_session():
    try:
        data = request.json
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
        name = request.GET.get("name")
        uername = request.GET.get("username")
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
        data = request.json
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
        name = request.GET.get("name")
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
        data = request.json
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
        data = request.json
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
        data = request.json
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
        data = request.json
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
        data = request.json
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
        data = request.json
        for node in grid:
            if node.name == data["node"]["name"]:
                cls = testgrid.parser.get_subclass(data["package"]["type"], testgrid.model.Package , data["package"]["module"])
                return {"result":node.is_installable(cls(name = data["package"]["name"], version = data["package"]["version"]))}
        return {"error": "node %s doesn't exist" % data["node"]["name"]}
    except Exception as e:
        return {"error": repr(e)}

@app.route('/get_nodes_session')
def get_nodes_session():
    name = request.GET.get("name")
    username = request.GET.get("username")
    session = get_session(username, name)
    result = {}
    nodes = []
    for node in session:
        nodes.append({"name": node.name ,"typename": node.get_typename(), "hoststring": node.hoststring})
    result["nodes"]  = nodes
    return result

if __name__ == '__main__':
    try:
        args = docopt.docopt(__doc__)
        grid = testgrid.parser.parse_grid(args["--grid"], args[ "--manifest"])
        app.run(host=args["--host"], port=args["--port"], debug=True)
    except Exception as e:
        print e
