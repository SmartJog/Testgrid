# copyright (c) 2014 arkena, released under the GPL license.

"local client for transient (=anonymous) sessions only"

import testgrid
import aksetup
import debian

class Session(testgrid.server.model.Session):

	def __init__(self):
		super(Session, self).__init__(
			grid = testgrid.server.parser.parse_grid("grid", "/home/sbideaux/localgrid.ini"),
			subnet = None, # FIXME
			key = None) # anonymous only as there is no controller process
