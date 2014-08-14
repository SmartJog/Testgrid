# copyright (c) 2014 smartjog, released under the GPL license.

# copyright (c) 2014 smartjog, released under the GPL license.                                                                                          

import ansible.playbook
from ansible import callbacks
from ansible import utils

class Playbook():
    def __init__(self, playbook_path = None, inventory = None,  callbacks = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY), runner_callbacks = ca\
llbacks.PlaybookRunnerCallbacks(callbacks.AggregateStats(), verbose=utils.VERBOSITY), stats = callbacks.AggregateStats()):

        self.playbook = ansible.playbook.PlayBook(playbook = playbook_path,inventory = inventory, callbacks = callbacks, runner_callbacks = runner_call\
backs, stats = stats)

    def run(self):
        return self.playbook.run()
