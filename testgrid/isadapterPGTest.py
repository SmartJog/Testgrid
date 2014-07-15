import testgrid
import unittest

class SelfTestPG(testgrid.isadapter.FakeTest):
	def setUp(self):
		#!!! VPN !!!
		self.grid = testgrid.isadapter.TempGrid(name = "testis_pg", hoststring = "root@hkvm-pg-1-1.pg-1.arkena.net", profile_path = "testgrid/profiles.json" , ipstore_host = "ipstore.qa.arkena.com",ipstore_port=80 ,dbpath = "/tmp/istest-pg.db")
		self.profile = "pg"


if __name__ == "__main__": unittest.main(verbosity = 2)
