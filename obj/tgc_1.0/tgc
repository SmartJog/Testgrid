"""
Usage:
  my_program --host NAME --port NAME --grid NAME --manifest INI

Options:
  -g NAME, --grid NAME       set grid section NAME in the manifest [default: grid]
  --host NAME                ...
  --port NAME                ...
  -m INI, --manifest INI     comma-separated list of .ini filepaths or URIs [default: ~/grid.ini]

"""
import docopt
import testgrid


if __name__ == '__main__':
    try:
        args = docopt.docopt(__doc__)
        g = testgrid.parser.parse_grid(args["--grid"], args["--manifest"])
        testgrid.controller.setup_serveur(host=args["--host"], port=args["--port"], g=g)
    except Exception as e:
        print e
