#!/usr/bin/env python
"""
Usage:
  my_program --host NAME --port NAME --grid NAME --manifest INI
  my_program --host NAME --port NAME

Options:
  -g NAME, --grid NAME       set grid section NAME in the manifest [default: grid]
  --host NAME                ...
  --port NAME                ...
  -m INI, --manifest INI     comma-separated list of .ini filepaths or URIs [default: /etc/tgc/grid.ini]

"""
import testgrid


if __name__ == '__main__':
    try:
        args = testgrid.docopt.docopt(__doc__)
        g = testgrid.parser.parse_grid(args["--grid"], args["--manifest"])
        testgrid.controller.setup_serveur(host=args["--host"], port=args["--port"], g=g)
    except Exception as e:
        print e
