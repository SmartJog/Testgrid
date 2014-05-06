Test Grid
=========

TestGrid (TG) is a service providing isolated, on-demand and Programmable Test Environments (PTE) to deploy quickly assets under test. The service can be used manually or integrated with automation tools to generate easily varying test conditions: components, configuration, connections, I/O and so on.

* * *

Features
--------

  * Sessions –
    A user interacts with the TG via persistent or transient sessions     (respectively for long-running tests and one-shot short tests.)
  * Allocation –
    The user provides nodes’ specs, TG picks the appropriate hosting platform,     and instantiates the nodes in the given session.
  * Deployment –
    The user provides packages’ specs,
    TG allocates appropriate nodes and installs the packages.
  * Isolation –
    All allocated nodes are pushed in a subnet to avoid side-effects.
  * Programmation –
    TG functions are accessible through its API to automate your work
    (Python API, CLI tool.)
  * Provisioning Ecosystem Integration –
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

Tutorial
--------

Coming soon!
