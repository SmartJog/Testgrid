import bottle
from bottle import route, request, Bottle, abort 
import impl
import model
import command
import sys
import json


SERVER_IP  = "192.168.0.8"
LOCALHOST = "127.0.0.1"

tg = impl.TestGrid(pathDatabase="testgrid.db")
app = Bottle()


def checkSession(user, password=None):
    if tg.session.exist(user):
        return True
    return False


@app.route("/ping")
def checkClient():
    login = request.GET.get("session")
    if login is not None:
        if checkSession(login) is True:
            return {"failure": 0, "message": ""}
        else:
            return {"failure": 1, "message": "user {0} doesn't exist".format(login) }
    else:
        newLogin = "testgridUser{0}".format(tg.session.maxId())
        tg.session.append(impl.Session(newLogin))
        return {"failure": 0, "newLogin": newLogin}
    

@app.route("/session")
def createSession():
    newLogin = "testgridUser{0}".format(tg.session.maxId())
    tg.session.append(impl.Session(newLogin))
    return "your testgrid login is %s\n" % newLogin

@app.post("/add")
def add():
    if request.remote_addr != tg.hostname:
        abort(401, "Sorry, access denied Sorry, access denied you must be admin to perform this task.")
    hosts = request.json['host']
    for host in hosts:
        if tg.nodes.exist(host["hostname"]) == False:
            if host["rootpass"]:
                node = command.Command.addNode(host["hostname"], host["rootpass"])
            else:
                return {"failure": 1, "message": "missing rootpass for host %d" % host["hostname"]}
            if node is  not None:
                tg.nodes.append(node)
                return {"failure": 0, "message":"successfully added %s" % host["hostname"]}
            else:
                return {"failure": 1, "message":"fail to add %s" % host["hostname"]}
        else:
            return {"failure": 1, "message":"%s already exist" % host["hostname"]}

@app.route("/list")
def listNode():
    if request.remote_addr != tg.hostname:
        abort(401, "Sorry, access denied Sorry, access denied you must be admin to perform this task.")
    listHost = list()
    for n in tg.nodes:
        listHost.append({"hostname": n.hostname, 
                         "username" :n.username, 
                         "userpass": n.userpass,
                         "rootpass": n.rootpass,
                         "operatingsystem": n.operatingsystem,
                         "available": n.available})
    data = json.dumps({"failure": 0, "host": listHost})
    return data
    

@app.route("/delete")
def delete():
    if request.remote_addr != tg.hostname:
        abort(401, "Sorry, access denied you must be admin to perform this task.")
    hostname = request.GET.get("hostname")
    if hostname is None:
        abort(400, "Bad request")
    if tg.nodes.remove(hostname):
        return {"failure": 0}
    return {"failure": 1}

@app.route("/deploy")
@bottle.auth_basic(checkSession)
def deployPackage():
    login = bottle.request.auth[0]
    packageName = request.GET.get("name")
    version = request.GET.get("version")
    if packageName is None:
        abort(400, "Bad request")
    session = tg.session.indexedSession(login)
    package =  model.Package(packageName, version)
    result = tg.deploy(session, package)
    return result


@app.route("/undeploy")
@bottle.auth_basic(checkSession)
def undeployPackage():
    index = request.GET.get("id")
    if tg.deployments.exist(index) == True and index is not None:
        result = tg.undeploy(index)
        return result
    else:
        return {"failure": 1}

@app.route("/deploymentlist")
@bottle.auth_basic(checkSession)
def listSessiondeployment():
    login = bottle.request.auth[0]
    session = tg.session.indexedSession(login)
    deploymentList = tg.deployments.listDeploymentSession(session)
    data = json.dumps({"failure": 0, "deployment": deploymentList})
    return data
    

@app.route("/user")
def getUserNodeInfo():
    hostname = request.GET.get("hostname")
    if hostname is None:
        abort(400, "Bad request")
    node = tg.nodes.indexedNode(hostname)
    if node is None:
        return {"failure": 1, "message": "Bad host {0}".format(hostname)}
    return {"failure": 0, "username": node.username, "password": node.userpass}

if __name__ == '__main__':
    tg.hostname = SERVER_IP
    if len(sys.argv) == 2:
        tg.hostname = sys.argv[1]
    try: 
        app.run(host=tg.hostname, port=8080, debug=True)
    except Exception as e:
        print e
