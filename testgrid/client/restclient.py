# copyright (c) 2014 arkena, released under the GPL license.

"local client for transient (=anonymous) sessions only"
import testgrid
from .. import common
#from ..common import simplifiedModel
#from simplifiedModel import Node 
#from simplifiedModel import responseObject
import requests
import json
import inspect 
import debian
import sys
import imp
import jsonpickle
from jsonpickle import handlers




class Session(common.simplifiedModel.Session):

	def __init__(self, host, port, key=None):
		super(Session, self).__init__(key = None) 
		self.host = host
		self.port = port
		self.session = requests.Session()
		self.session.auth = (self.key, None)


	def __del__(self):pass
	#if is_anonymous (undeploy all workflow)

	

	def allocate_node(self, sysname = None, pkg = None):
		url = 'http://{0}:{1}/allocate'.format(self.host, 
						       self.port)
		r = self.session.get(url)
		res = jsonpickle.decode(r.text)
	        return res

	

	#def deploy(self, *packages):
		

