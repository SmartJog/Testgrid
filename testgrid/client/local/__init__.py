# copyright (c) 2014 arkena, released under the GPL license.

"local client for transient (=anonymous) sessions only"

import aksetup
import debian
import testgrid

class Session(testgrid.server.model.Session):

	def __init__(self, mode):
		assert mode in ("eth2lan", "en0wifi")
		if mode == "eth2lan":
			cls = testgrid.server.testbox.Eth2Lan
		else:
			cls = testgrid.server.testbox.En0Wifi
		super(Session, self).__init__(
			grid = (cls)(),
			subnet = None, # FIXME
			key = None) # anonymous only as there is no controller process
