import testgrid
from testgrid import common
import model
import parser
import bottle
import bottle 
import copy
import jsonpickle


tg = parser.parse_grid("grid", "~/grid.ini")
app = bottle.Bottle()


def createJson(is_failure, msg=None, data=None):
    response = common.simplifiedModel.responseObject(is_failure, msg, data)
    pick =  jsonpickle.encode(response)
    return pick



class ServerError(Exception): pass

@app.route("/ping")
def checkClient():
    login = bottle.request.GET.get("session")
    if login is  None:
        return createJson(1, "login is missing")

    is_anonymous = bottle.request.GET.get("session")
    if is_anonymous is  None:
        return createJson(1, "anonymous status is missing")
    return createJson(0, "pong")

@app.route("/allocate")
def allocate_node():
    session = model.Session(tg,None,  key= bottle.request.GET.get("session"))
    node = session.allocate_node()
    return createJson(1, "success", common.simplifiedModel.Node(node.hoststring))
    

if __name__ == "__main__":
    app.run(host=tg.host, port=tg.port, debug=True)
