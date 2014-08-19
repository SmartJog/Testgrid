#copyright (c) 2014 arkena, released under the GPL license.

import ansible.playbook
from ansible import callbacks
from ansible import utils
import testgrid
import httplib
import urllib2
import tempfile, textwrap

class Playbook():
    def __init__(self, pkg_name, session,
                 callbacks = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY),
                 runner_callbacks = callbacks.PlaybookRunnerCallbacks(callbacks.AggregateStats(),
                                                                      verbose=utils.VERBOSITY), 
                 stats = callbacks.AggregateStats()):
        parser = testgrid.parser.Parser(ini= "/etc/tg/web-server.ini")
        if parser.conf.has_section("tg-web-server"):
            self.host = parser.conf.get('tg-web-server', 'host')
            self.port = parser.conf.get('tg-web-server', 'port')
            self.ssh_key = parser.conf.get('tg-web-server', 'ssh_key')
        else:
            raise Exception("web-server bad config file")
        ini = self._get_pkg_ini(pkg_name)
        f = tempfile.NamedTemporaryFile()
        f.write(textwrap.dedent(ini))
        f.flush()
        nodes_opts, opt = testgrid.parser.parse_session(pkg_name, f.name)
        inventory = testgrid.inventory.Inventory(opt["inventory_path"])
        inventory.update_inventory(session, nodes_opts)
        self.playbook = ansible.playbook.PlayBook(playbook = opt["playbook_path"],
                                                  inventory = inventory.inventory,
                                                  callbacks = callbacks,
                                                  runner_callbacks = runner_callbacks, 
                                                  stats = stats, private_key_file = self.ssh_key)

    def _get_pkg_ini(self, pkg_name):
        #get playbook description from web server
        response = urllib2.urlopen("http://%s:%s/ini/%s.ini" % (self.host, self.port, pkg_name))
        res = response.read()
        return res

    def run(self):
        return self.playbook.run()




