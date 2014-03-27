import model


class Grid(model.Grid):

    def __init__(self, host, port, nodes=[], *args, **kwargs):
        super(Grid, self).__init__(nodes, *args, **kwargs)
        self.host = host
        self.port = port
        self.nodes = nodes
