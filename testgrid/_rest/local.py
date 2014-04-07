# copyright (c) 2014 arkena, released under the GPL license.

"local client for transient (=anonymous) sessions only"

import testgrid
import aksetup
import debian
import requests
import json


class responseObject(object):
	def __init__(self, failure, msg, data):
		self.failure = failure
		self.msg = msg
		self.data = data

def decodeJson(json, objectSignature):
	return objectSignature(json["failure"], json["message"], json["data"])
            


class Session(testgrid.server.model.Session):

	def __init__(self, host, port, key=None):
		super(Session, self).__init__(
			grid = None,
			subnet = None, # FIXME
			key = None) # anonymous only as there is no controller process
		self.host = host
		self.port = port
		self.session = requests.Session()
		self.session.auth = (self.key, None)
		self.check_server()


	def __del__(self):pass
	#if is_anonymous (undeploy all workflow)

	def check_server(self):
		url = 'http://{0}:{1}/ping?session={2}?anonymous={3}'.format(self.host, 
									     self.port, 
									     self.key, 
									     self.is_anonymous)
		response = requests.get(url)
		json = response.json()
		print json
		jsonObject = decodeJson(json, responseObject)

	def allocate_node(self, sysname = None, pkg = None):pass


	def release_node(self, node):pass

	def deploy(self, *packages):pass
		
		#url = 'http://{0}:{1}/deploy?name={2}&version={3}'.format(self.host, 
		#							  self.port, 
		#							  arg['<packagename>'], 
		#							  arg['--version'])


	def undeploy(self):pass



