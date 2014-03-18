import ConfigParser
import factory
import model
import debian
class ConfigurationError(Exception): pass

class GridConfig(object):
    def __init__(self, gridName, fileName):
        self.config = ConfigParser.RawConfigParser()
        self.config.read(fileName)
	self.gridName = gridName

    def getGridType(self):
        if not self.config.has_section(self.gridName):
            raise(ConfigurationError)
        return self.config.get(self.gridName, 'type')
        

    def getNodesInfo(self):
        nodeInfo = []
        nodes =  self.config.get(self.gridName , 'nodes')
        for n in nodes.split(' '):
            if not self.config.has_section(n):
                raise(ConfigurationError)
            nodeInfo.append((self.config.get(n, 'type'), self.config.get(n, 'hoststring')))
        return tuple(nodeInfo)




def parse_grid(name, ini):
	"parse manifests and return a grid instance"
	nodes = []
	config = GridConfig(name, ini)
	gridType = config.getGridType()
	nodeParent = factory.Factory.getClass("model", "Node")
	nodesInfo = config.getNodesInfo()
	for nodeType, hoststring in nodesInfo:
		nodes.append(factory.Factory.generateSubclass(nodeParent, 
							     nodeType, 
							     hoststring=hoststring))
	gridParent = factory.Factory.getClass("model", "Grid")
	grid = factory.Factory.generateSubclass(gridParent, gridType, nodes=nodes)
        return grid


#parse_grid("grid", "config.ini")


	
	



