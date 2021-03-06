# copyright (c) 2013-2014 smartjog, released under the GPL license.

import setuptools

setuptools.setup(
	name = "testgrid",
	version = "0.1",
	author = "arkena",
	author_email = "qa@tdf-ms.com",
	description = "Programmable test environments framework and command-line utility",
	license = "GPL",
	packages = (
		"testgrid",
		"testgrid.client",
		"testgrid.server"),
	entry_points = { "console_scripts": "tg = testgrid.main:main" },
)
