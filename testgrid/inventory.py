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
            try:
                self.name = inventory_file
                self.inventory = ansible.inventory.Inventory(inventory_file)
            except Exception as e:
                raise Exception("error parsing %s: %s" % (inventory_file, e))

        def update_inventory(self, session, nodes_opt):
                "update inventory hostname"
                if len(session) == 0:
                        self._allocate_inventory_nodes(session, nodes_opt)
                elif len(session) >= len(nodes_opt):
                        self._verify_allocated_node(session, nodes_opt)
                else:
                        raise Exception("session %s contains only %d nodes, %d are requested", session.name, len(session), len(nodes_opt))

        def _allocate_inventory_nodes(self, session, nodes_opt):
            for opt in nodes_opt:
                try:
                    host =  self.inventory.get_host(opt["name"])
                    del opt["name"]
                    if not host:
                        raise Exception("node %s hasn't been found in the inventory file %s" % (opt["name"], self.name))
                    node = session.allocate_node(**opt)
                    host.set_variable("ansible_ssh_host", node.get_hoststring())
                    #ip
                except Exception as e:
                        session.close()
                        raise e

        def _verify_allocated_node(self, session, nodes_opt):
                excluded = []
                for opt in nodes_opt:
                        role = opt["name"]
                        del opt["name"]
                        for node in session:
                                if node.has_support(**opt) and  not node in excluded:
                                        host =  self.inventory.get_host(role)
                                        host.set_variable("ansible_ssh_host", node.get_hoststring())
                                        excluded.append(node)
                                        break
                if len(excluded) < len(nodes_opt):
                        raise Exception("session %s doesn't support enough requested node", session.name)

        def get_inventory_group(self):
                result = {}
                groups = self.inventory.get_groups()
                for group in groups:
                        children = []
                        for child in group.child_groups:
                                children.append(child.name)
                        host_names = self.inventory.list_hosts(pattern = group.name)
                        result[group.name] = {"hosts": host_names, "vars": group.get_variables(), "children": children}
                return result

        def get_host_variables(self, hostname):
                host = self.inventory.get_host(hostname)
                return host.get_variables()

        def get_all_hosts(self):
                #review _meta
                hosts = {"hostvars": {}}
                for host in self.inventory.get_hosts():
                        hosts["hostvars"][host.name] = host.get_variables()
                return {"_meta": hosts}


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
                return testgrid.model.Hoststring(self.hostname)


class FakeGrid(testgrid.model.Grid):pass

import tempfile
import textwrap
import os
import stat
import subprocess
import shlex

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
                group1""")

                session_ini = self.get_file("""
                [task1]
                sysname = Debian

                [task2]
                sysname = Windows

                [test]
                nodes = task1 task2""")

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
                nodes = node1 node2""")
                client = testgrid.client.Client(testgrid.parser.parse_grid("grid",
                                                                           grid_ini.name ,
                                                                           __name__))
                nodes_opt = testgrid.parser.parse_session("test", session_ini.name)
                session = client.open_session("test")
                inventory = Inventory(inventory_file.name)
                inventory.update_inventory(session, nodes_opt)
                result = inventory.get_inventory_group()
                host_var = inventory.get_host_variables("task1")
                script = ("#!/usr/bin/python\n"
                          "import json\n"
                          "import sys\n"
                          "groups = %s\n"
                          "vars  = %s\n"
                          "if __name__ == '__main__':\n"
                          "    if len(sys.argv) == 2 and (sys.argv[1] == '--list'):\n"
                          "        print json.dumps(groups, indent=4)\n"
                          "    elif len(sys.argv) == 3 and (sys.argv[1] == '--host'):\n"
                          "        print json.dumps(vars, indent=4)\n"
                          "    else:\n"
                          "        print \"Usage: --list or --host <hostname>\"\n"
                          "    sys.exit(1)\n") % (repr(result), repr(host_var))
                # f = open("test_inventory.py", "w+")
                # f.write(textwrap.dedent(script))
                # st = os.stat(f.name)
                # os.chmod(f.name, st.st_mode | stat.S_IEXEC)
                # command = ['chmod +x %s' % f.name,'ansible -i %s --list-hosts all' % f.name]
                # process = subprocess.Popen('chmod +x %s;ansible -i %s --list-hosts all' % (f.name, f.name), shell=True)
                # print process

if __name__  == "__main__": unittest.main(verbosity = 2)

