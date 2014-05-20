#!/usr/bin/python

"""
script that uses a testgrid session as an inventory file
Usage:
  my_program --list
  my_program --host <hostname>

Options:
   --list                               return a JSON hash/dictionary of all the groups to be managed
   --host <hostname>                    return either an empty JSON hash/dictionary, or a hash/dictionary of variables to make available to templates and playbooks
"""
import docopt
import testgrid
import sys
import json

__version__ = "0.1"

grid = {{ grid }}
client_is_local = {{ client_is_local }}
manifest = None #{{ manifest }}
hostring = None #{{ hostring }}
inventory = {{ inventory }}
session_ini = {{ session_ini }}
session_name = {{ session_name }}
client_arg = {{client_arg}} #manifest or hoststring
modules = {{modules}}

if __name__ == "__main__":
    try:
        args = docopt.docopt(__doc__)
        if client_is_local:
            client = testgrid.local.Client(name = grid,
                                           ini = client_arg, modules= modules)
        else:
            client = testgrid.rest.Client(client_arg)
        nodes_opts = testgrid.parser.parse_session(session_name, session_ini)
        session = client.open_session(session_name)
        inventory_obj = testgrid.inventory.Inventory(inventory)
        inventory_obj.update_inventory(session, nodes_opts)
        if args["--list"]:
            print json.dumps(inventory_obj.get_inventory_group(), indent=4)
        elif args["--host"]:
            print json.dumps(inventory_obj.get_host_variables(args["--host"]), indent=4)
    except Exception as e:
        sys.stderr.write("%s: %s\n" % (type(e).__name__, e))
