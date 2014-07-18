import testgrid
import unittest, time

class SelfTestPG(testgrid.isadapter.FakeTest):
	def setUp(self):
		#!!! VPN !!!
		self.grid = testgrid.isadapter.TempGrid(name = "testis_pg", hoststring = "root@hkvm-pg-1-1.pg-1.arkena.net", profile_path = "testgrid/profiles.json" , ipstore_host = "ipstore.qa.arkena.com",ipstore_port=80 ,dbpath = "/tmp/istest-pg.db")
		self.profile = "pg"
                self.opts = {"image_name": "debian-smartjog",
                             "profile_name": self.profile,
                             "name": "test-isadapter-%s"
                             % time.strftime("%Y%m%d%H%M%S", time.localtime())}

if __name__ == "__main__": unittest.main(verbosity = 2)
