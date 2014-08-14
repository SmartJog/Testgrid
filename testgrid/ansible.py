# copyright (c) 2014 smartjog, released under the GPL license.

import ansible

class Playbook():
    def __init__(self):
        self.playbook = ansible.PlayBook( playbook_path = None,inventory = None)

    def _run():
        return self.playbook.run()
