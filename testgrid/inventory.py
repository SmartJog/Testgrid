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
import jinja2
import os
import stat

class Inventory(object):

        def __init__(self, inventory_file):
            try:
                self.name = inventory_file
                self.inventory = ansible.inventory.Inventory(inventory_file)
            except Exception as e:
                raise Exception("error parsing %s: %s" % (inventory_file, e))

        def update_inventory(self, session, nodes_opt):
                "update inventory host using host from testgrid"
                if len(session) == 0:
                        self._allocate_inventory_nodes(session, nodes_opt)
                elif len(session) >= len(nodes_opt):
                        self._verify_allocated_node(session, nodes_opt)
                else:
                        raise Exception("session %s contains only %d nodes, %d are requested", session.name, len(session), len(nodes_opt))

        def _allocate_inventory_nodes(self, session, nodes_opts):
                for opts in nodes_opts:
                        try:
                                host =  self.inventory.get_host(opts["name"])
                                #del opts["name"]
                                if not host:
                                        raise Exception("node %s hasn't been found in the inventory file %s" % (opts["name"], self.name))
                                node = session.allocate_node(**opts)
                                host.set_variable("ansible_ssh_host", node.get_hoststring())
                                host.set_variable("ip", node.get_hoststring())
                        except Exception as e:
                                session.close()
                                raise Exception("allocate_inventory_nodes %s" % e)

        def _verify_allocated_node(self, session, nodes_opts):
                excluded = []
                for opts in nodes_opts:
                        for node in session:
                                if node.has_support(**{key:opts[key] for key in opts if key!="name"}) and  not node in excluded:
                                        host =  self.inventory.get_host(opts["name"])
                                        host.set_variable("ansible_ssh_host", node.get_hoststring())
                                        host.set_variable("ip", node.get_hoststring()) # same as ansible_ssh_host motherbrain requires it
                                        excluded.append(node)
                                        break
                if len(excluded) < len(nodes_opts):
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
                #review _meta for optimization
                hosts = {"hostvars": {}}
                for host in self.inventory.get_hosts():
                        hosts["hostvars"][host.name] = host.get_variables()
                return {"_meta": hosts}

def generate_inventory_script(inventory, session, session_ini , is_local , client_arg, grid = None, *modules):
        env = jinja2.Environment()
        env.loader = jinja2.FileSystemLoader(os.path.dirname(os.path.abspath(__file__)))
        tmpl = env.get_template('template_inventory.py')
        script = tmpl.render(grid="\"%s\"" % grid , client_is_local=is_local,
                             client_arg="\"%s\"" % client_arg,
                             inventory="\"%s\"" %inventory,
                             session_name= "\"%s\""  % session,
                             session_ini="\"%s\"" % session_ini, modules= modules)
        f = open("%s.py" % session, "w+")
        f.write(script)
        st = os.stat(f.name)
        os.chmod(f.name, st.st_mode | stat.S_IEXEC)

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
import subprocess
import shlex

class setupInventoryTest(object):
        def __init__(self, inventory, session, session_ini, grid_ini):
                self.inventory_file = inventory
                self.session = session
                self.session_ini = session_ini
                self.session = session
                self.grid_ini = grid_ini

        def __del__(self):
                if os.path.exists("%s.py" % self.session):
                        os.remove("%s.py" % self.session)

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

                                [test_basic_inventory_file]
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

                setup = setupInventoryTest(inventory_file, "test_basic_inventory_file", session_ini, grid_ini)
                generate_inventory_script(setup.inventory_file.name, setup.session,
                                          setup.session_ini.name ,
                                          True , setup.grid_ini.name, "grid", "testgrid.inventory")
                out = subprocess.check_output('ansible -i  %s.py --list-hosts group1' % setup.session, shell=True) #fix passwd issue
                self.assertIn("task1", out)


if __name__  == "__main__": unittest.main(verbosity = 2)

