class commandName:
    ADD = 'add'
    LIST = 'list'
    RM = 'rm'

class argName:
    HOSTNAME = "hostname"

class helpDescription:
    ADD = 'add node in testgrid'
    LIST = 'List testgrid node'
    RM = 'delete specific node'
    COMMAND = 'commands'
class helpArgDescription:
    ADD = 'hostname of the new node'
    RM = 'hostname of the node to delete'

class parserAttributes:
    NARGS = '+'
