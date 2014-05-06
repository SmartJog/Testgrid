Test Grid
=========

TestGrid (TG) is a service providing isolated, on-demand and programmable
test environments (TE) to deploy quickly assets under test.

A programmable TE allows to vary easily the test conditions: components,
configuration, connections, I/O and so on.

Features:

  * Sessions
    A user interacts with the TG via persistent or transient sessions     (respectively for long-running tests and one-shot short tests.)
  * Allocation
    The user provides nodes’ specs, TG picks the appropriate hosting platform,     and instantiates the nodes in the given session.
  * Deployment
    The user provides packages’ specs,
    TG allocates appropriate nodes and installs the packages.
  * Isolation
    All allocated nodes are pushed in a subnet to avoid side-effects.
  * Programmation
    TG functions are accessible through its API to automate your work
    (Python API, CLI tool.)
  * Provisioning Ecosystem Integration
    A TG session can be fed to ansible as a dynamic inventory

Installation
------------

	$ git clone git@git.smartjog.net:qa/testgrid.git
	$ cd testgrid
	(...)
	$ python setup.py install

Tutorial
--------

Coming soon!