# copyright (c) 2013-2014 smartjog, released under the GPL license.

"""
inventory-generator tool that will use testgrid to provide an inventory file to  ansible

"""
import unittest
import ansible
import sys
import json
import  sys
import testgrid

class Inventory(object):

    def __init__(self, inventory_file):
        "return inventory object"
        try:
            self.name = inventory_file
            self.inventory = ansible.inventory.Inventory(inventory_file)
        except Exception as e:
            raise Exception("error parsing %s: %s" % (inventory_file, e))

    def update_inventory(self, session, nodes_opt):
        nodes = []
        for opt in nodes_opt:
            try:
                host =  self.inventory.get_host(opt["name"])
                if not host:
                    raise Exception("node %s hasn't been found in the inventory file %s" % (opt["name"], self.name))
                node = session.allocate_node(**opt)
                nodes.append(node)
                host.set_variable("ansible_ssh_host", node.get_hoststring())
                host.get_variables()
            except Exception as e:
                for n in nodes:
                    session.release_node(n)
                    raise e

    def get_inventory_group(self):
        result = {}
        groups = self.inventory.get_groups()
        for group in groups:
            host_names = self.inventory.list_hosts(pattern = group.name)
            result[group.name] = {"hosts": host_names, "vars": group.get_variables()}
            #FIX CHILDREN
        return result

    def get_host_variables(self, hostname):
        host = self.inventory.get_host(hostname)
        return host.get_variables()

##############
# unit tests #
##############
class FakeNode(testgrid.model.FakeNode):

    def __init__(self, name, hostname, sysname):
        super(FakeNode, self).__init__(name = name)
        self.name = name
        self.sysname = sysname
        self.hostname = hostname

    def __eq__(self, other):
        if type(self) == type(other):
            if self.name == other.name:
                return True
            return False

        def __ne__(self, other):
                return not (self == other)

    def has_support(self, sysname = None, **opts):
        return True

    def get_hoststring(self):
        return self.hostname


class FakeGrid(testgrid.model.Grid):pass

import tempfile
import textwrap
import os
import stat

class SelfTest(unittest.TestCase):
    @staticmethod
    def get_file(content = ""):
        "generate a temporary file with the specified content"
        f = tempfile.NamedTemporaryFile()
        f.write(textwrap.dedent(content))
        f.flush()
        return f

    def test_basic_inventory_file(self):
        inventory_file = self.get_file("""
            task1 host=test.com
            task2 host=test2.com

                 [group1]
                 task1

                 [group2]
                 task2

                 [group1:vars]
                 var = "var group one"

                 [group2:vars]
                 var = "var group 2"

                 [group2:children]
                 group1
        """)

        session_ini = self.get_file("""
                      [task1]
                      sysname = Debian

                      [task2]
                      sysname = Windows

                      [test]
                      nodes = task1 task2
                      """)
        grid_ini = self.get_file("""
                             [node1]
                             type = fake node
                             hostname = testnode1
                             sysname = Debian

                             [node2]
                             type = fake node
                             hostname = testnode2
                             sysname = Windows

                             [grid]
                             type = fake grid
                             nodes = node1 node2 node3
                             """)
        client = testgrid.client.Client(testgrid.parser.parse_grid("grid",  grid_ini.name , __name__))
        nodes_opt = testgrid.parser.parse_session("test", session_ini.name)
        session = client.open_session("test")
        inventory = Inventory(inventory_file.name)
        inventory.update_inventory(session, nodes_opt)
        result = inventory.get_inventory_group()
        host_var = inventory.get_host_variables("task1")
        script = """#!/usr/bin/python
import json
import sys

groups = %s
vars  = %s
if __name__ == '__main__':
    if len(sys.argv) == 2 and (sys.argv[1] == '--list'):
        print json.dumps(groups, indent=4)
    elif len(sys.argv) == 3 and (sys.argv[1] == '--host'):
        print json.dumps(vars, indent=4)
    else:
        print "Usage: --list or --host <hostname>"
        sys.exit(1)
                 """ % (repr(result), repr(host_var))
        f = open("test_inventory.py", "w+")
        f.write(textwrap.dedent(script))
        st = os.stat(f.name)
        os.chmod(f.name, st.st_mode | stat.S_IEXEC)

if __name__  == "__main__": unittest.main(verbosity = 2)

