# copyright (c) 2013-2014 smartjog, released under the GPL license.

import setuptools
import testgrid.main

setuptools.setup(
	name = "testgrid",
	version = main.__version__,
	author = "arkena",
	author_email = "qa@tdf-ms.com",
	description = "Programmable test environments framework and command-line utility",
	license = "GPL",
	packages = (
		"testgrid",
		"testgrid.client",
		"testgrid.client.fake",
		"testgrid.client.local",
		"testgrid.client.rest",
		"testgrid.server"),
	entry_points = { "console_scripts": "tg = testgrid.main:main" },
)
