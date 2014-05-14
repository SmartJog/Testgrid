"""
Usage:
  my_program --host HOST --port PORT --grid NAME --manifest NAME

"""
import docopt
import bottle
from bottle import route, request, Bottle, abort
import parser
import sys
import model
import debian
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
            return ({"result": grid.is_quarantined()})
    return ({"error": "node %s doesn' exist" % name})

@app.post("/deploy")
def deploy():
    try:
        data = request.json
        list_packages = []
        for package in data["packages"]:
            cls = parser.get_subclass(package["type"], testgrid.model.Package ,package["module"])
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


if __name__ == '__main__':
    if len(sys.argv) == 4:
        try:
            grid = parser.parse_grid(sys.argv[2], sys.argv[3])
            app.run(host=sys.argv[1], port="8080", debug=True)
        except Exception as e:
            print e
