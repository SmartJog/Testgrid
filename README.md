	████████╗███████╗███████╗████████╗ ██████╗ ██████╗ ██╗██████╗ 
	╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝██╔════╝ ██╔══██╗██║██╔══██╗
	   ██║   █████╗  ███████╗   ██║   ██║  ███╗██████╔╝██║██║  ██║
	   ██║   ██╔══╝  ╚════██║   ██║   ██║   ██║██╔══██╗██║██║  ██║
	   ██║   ███████╗███████║   ██║   ╚██████╔╝██║  ██║██║██████╔╝
	   ╚═╝   ╚══════╝╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝ 

* * *

TestGrid (TG) is a PTE (Programmable Test Environments) provider.
The service can use local single-user resources or shared remote resources;
it can also be used manually or integrated to automation tools like Jenkins.

* * *

Features
--------

  * **Sessions**
    A user interacts with the TG via sessions.
  * **Allocation**
    The user provides nodes’ specs, TG picks the appropriate hosting platform,     and instantiates the nodes in the given session.
  * **Deployment**
    The user provides packages’ specs,
    TG allocates appropriate nodes and installs the packages.
  * **Isolation**
    All allocated nodes are pushed in a subnet to avoid side-effects.
  * **Programmation**
    TG functions are accessible through its API to automate your work
    (Python API, CLI tool.)
  * **Provisioning Ecosystem Integration**
    A TG session can be fed to ansible as a dynamic inventory

Requirements
------------

  * python 2.7
  * Ubuntu 13.x | Debian 7 | OS/X Mavericks

Dependencies
------------

  * python-setuptools
  * python-ansible

Installation
------------

	$ git clone git@git.smartjog.net:qa/testgrid.git
	$ cd testgrid
	$ python setup.py install

Python API Example
------------------

	>>> import testgrid
	>>> client = testgrid.rest.Client()
	>>> session = client.open_session("helloworld")
	>>> fleche = client.get_package(name = "fleche", version = "16.3-1")
	>>> session.deploy(fleche)
	>>> node = session.allocate_node(is_image = "cdn-itransmux", profile = "cdn:basic")
	>>> while not all(node.is_up() for node in session): sleep(1)
	>>> map(node.execute("uname") for node in session)
	["Linux", "Linux"]
	>>> session.close()

Credits
-------

  * ascii art generator: http://patorjk.com/software/taag/#p=display&f=Graffiti&t=