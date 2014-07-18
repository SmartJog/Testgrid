import testgrid
import unittest, time

class SelfTestQAP(testgrid.isadapter.FakeTest):
	def setUp(self):
		#!!! VPN !!!
		self.grid = testgrid.isadapter.TempGrid(name = "testis_qap", hoststring = "root@10.69.44.1", profile_path = "testgrid/profiles.json" , ipstore_host = "ipstore.qa.arkena.com",ipstore_port=80 ,dbpath = "/tmp/istest-qap.db")
		self.profile = "tg:basic"
                self.opts = {"image_name": "debian-smartjog",
                             "profile_name": self.profile,
                             "name": "test-isadapter-%s"
                             % time.strftime("%Y%m%d%H%M%S", time.localtime())}

if __name__ == "__main__": unittest.main(verbosity = 2)
