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
app = Bottle()
grid = None

class DebianPackage(debian.Package): pass

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

@app.route("/deploy")
def deploy():
    try:
        packages = request.GET.getall("pkg")
        list_packages = []
        for value in packages:
            pkg, pkg_type = value.partition(" ")[::2]
            pkg_name, pkg_version = pkg.partition("=")[::2]
            #parser package type
            list_packages.append(debian.Package(name = pkg_name, version = pkg_version))
        session = request.GET.get("session")
        username, name = session.partition(" ")[::2]
        session_obj = grid.open_session(username, name)
        plans = session_obj.deploy(list_packages)
        result = {}
        for pkg, node in plans:
            result[node.name] = {"pkg":(pkg.name, pkg.version), "args": {"typename": node.get_typename(), "hoststring": node.hoststring}}
        return result
    except Exception as e:
        return {"error": repr(e)}

@app.route("/undeploy")
def undeploy():
    session = request.GET.get("session")
    username, name = session.partition(" ")[::2]
    session_obj = grid.open_session(username, name)
    session_obj.undeploy()
    return {"result": True}

@app.route("/open_session")
def open_session():
    username = request.GET.get("username")
    name = request.GET.get("name")
    session = grid.open_session(username, name)
    return {"result": True}

@app.route("/allocate_node")
def allocate_node():
    session = request.GET.get("session")
    username, name = session.partition(" ")[::2]
    session_obj = grid.open_session(username, name)
    print request.GET.items()

if __name__ == '__main__':
    if len(sys.argv) == 4:
        try:
            grid = parser.parse_grid(sys.argv[2], sys.argv[3])
            app.run(host=sys.argv[1], port="8080", debug=True)
        except Exception as e:
            print e
