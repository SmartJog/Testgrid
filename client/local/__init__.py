# copyright (c) 2014 arkena, released under the GPL license.

"local client for transient (=anonymous) sessions only"

import aksetup
import debian
import server

class Session(server.model.Session):

	def __init__(self):
		super(Session, self).__init__(
			grid = server.testbox.En0Wifi(),
			subnet = None, # FIXME
			key = None) # anonymous only as there is no controller process
