# copyright (c) 2014 arkena, all rights reserved.

import setuptools

setuptools.setup(
	name = "testgrid",
	version = "0.1",
	author = "arkena",
	author_email = "qa@tdf-ms.com",
	description = "Programmable test environments framework and command-line utility",
	license = "GPL",
	packages = ("testgrid", "testgrid.client", "testgrid.client.local", "testgrid.server"),
	entry_points = { "console_scripts": "tg = testgrid.main:main" },
)
