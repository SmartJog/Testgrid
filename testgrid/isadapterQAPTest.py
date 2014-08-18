#copyright (c) 2014 arkena, released under the GPL license.

import testgrid
import unittest, time

class SelfTestQAP(testgrid.isadapter.FakeTest):
	def setUp(self):
		#!!! VPN !!!
		self.grid = testgrid.isadapter.TempGrid(name = "testis_qap", hoststring = "root@10.69.44.2", profile_path = "testgrid/profiles.json" , ipstore_host = "ipstore.qa.arkena.com",ipstore_port=80 ,dbpath = "/tmp/istest-qap.db", public_key="~/.ssh/id_rsa.pub")
		self.profile = "tg:basic"
                self.opts = {"image_name": "debian-smartjog",
                             "profile_name": self.profile}

if __name__ == "__main__": unittest.main(verbosity = 2)
