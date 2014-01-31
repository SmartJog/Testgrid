import bottle
from bottle import route, request, Bottle, abort 
import impl
import model
import command
import sys

SERVER_IP  = "192.168.0.8"
LOCALHOST = "127.0.0.1"

tg = impl.TestGrid(pathDatabase="testgrid.db")
app = Bottle()

#def list_filter(config):
#    ''' Matches a comma separated list of numbers. '''
#    delimiter = config or ':'
#    regexp = r'\d+(%s\d)*' % bottle.re.escape(delimiter)
#
#    def to_python(match):
#        return map(int, match.split(delimiter))
#
#    def to_url(numbers):
#        return delimiter.join(map(str, numbers))
#
#    return regexp, to_python, to_url
#
#app.router.add_filter('list', list_filter)

def checkSession(user, password):
    if tg.session.exist(user):
        return True
    return False




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
            node = command.Command.addNode(host["hostname"], host["rootpass"])
            print "host to add %s" % host["hostname"]
            if node is  not None:
                tg.nodes.append(node)
                print "successfully added %s" % host["hostname"]
            else:
                print "fail to add %s" % host["hostname"]

@app.route("/list")
def listNode():
    if request.remote_addr != tg.hostname:
        abort(401, "Sorry, access denied Sorry, access denied you must be admin to perform this task.")
    for n in tg.nodes:
            print n.hostname

@app.route("/delete")
def delete():
    if request.remote_addr != tg.hostname:
        abort(401, "Sorry, access denied you must be admin to perform this task.")
    hostname = request.GET.get("hostname")
    if hostname is None:
        abort(400, "Bad request")
    tg.nodes.remove(hostname)
    #undeploy everything
    return "delete\n"

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
        abort(400, "Bad request")

@app.route("/deployment")
@bottle.auth_basic(checkSession)
def listSessiondeployment():
    login = bottle.request.auth[0]
    session = tg.session.indexedSession(login)
    deploymentList = tg.deployments.listDeploymentSession(session)
    print "deployment-id\tpackageName\tversion\t\tip\t"
    for item  in deploymentList:
        print "{0}\t\t{1}\t\t{2}\t\t{3}".format(item['index'], item['packageName'], item['version'], item['host'])
    #print "no deployment for %s" % login

@app.route("/user")
def getUserNodeInfo():
    hostname = request.GET.get("hostname")
    if hostname is None:
        abort(400, "Bad request")
    node = tg.nodes.indexedNode(hostname)
    if node is None:
        abort(400, "Bad request host not found")
    return "username: {0} password: {1} for host: {2}".format(node.username, node.userpass, hostname)

if __name__ == '__main__':
    tg.hostname = SERVER_IP
    if len(sys.argv) == 2:
        tg.hostname = sys.argv[1]
    try: 
        app.run(host=tg.hostname, port=8080, debug=True)
    except Exception as e:
        print e
