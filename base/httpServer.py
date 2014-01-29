import bottle
from bottle import route, request, Bottle, re, template 
import impl
import model
import command

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
    if request.remote_addr != SERVER_IP:
        return "you must be admin to perform this task\n"
    hosts = request.json['host']
    for host in hosts:
        if tg.nodes.exist(host["hostname"]) == False:    
            node = command.Command.addNode(host["hostname"], host["rootpass"])
            if node is  not None:
                tg.nodes.append(node)

@app.route("/delete/<hostname>")
def delete(hostname):
    if request.remote_addr != SERVER_IP:
        return "you must be admin to perform this task\n"
    tg.nodes.remove(hostname)
    return "delete\n"

@app.route("/deploy/<packageName>/<version>")
@bottle.auth_basic(checkSession)
def deployPackage(packageName, version):
    login = bottle.request.auth[0]
    session = tg.session.indexedSession(login)
    package =  model.Package(packageName, version)

 
@app.route("/list")
@bottle.auth_basic(checkSession)
def listSessiondeployment():pass


if __name__ == '__main__':
    app.run(host=SERVER_IP, port=8080, debug=True)
