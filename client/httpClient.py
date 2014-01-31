"""
Usage:
   my_program start <host> <port> [--username=<login>]

Options:
    --username=<login>
"""
import json
import requests
import sys
import cmd
from docopt import docopt, DocoptExit


def docopt_cmd(func):
    """
This decorator is used to simplify the try/except block and pass the result
of the docopt parsing to the called action.
"""
    def fn(self, arg):
        try:
            opt = docopt(fn.__doc__, arg)

        except DocoptExit as e:
            # The DocoptExit is thrown when the args do not match.
            # We print a message to the user and the usage block.

            print('Invalid Command!')
            print(e)
            return

        except SystemExit:
            # The SystemExit exception prints the usage for --help
            # We do not need to do the print here.

            return

        return func(self, opt)

    fn.__name__ = func.__name__
    fn.__doc__ = func.__doc__
    fn.__dict__.update(func.__dict__)
    return fn


class  Command(cmd.Cmd):

    file = None
    def __init__(self, host, port, username="unknownUser >"):
        self.host = host
        self.port = port
        self.intro = 'Welcome to testgrid client!'
        if username is None:
            self.prompt = "unknownUser >"
        else:
            self.prompt = username
        cmd.Cmd.__init__(self)

    @docopt_cmd
    def do_tcp(self, arg):
        """Usage: tcp <host> <port> [--timeout=<seconds>]"""

    @docopt_cmd
    def do_add(self, arg):
        """Usage: add <host> <password>"""
        try:
            url = 'http://{0}:{1}/add'.format(self.host, self.port)
            print arg['<host>']
            response = {"host": [{ "hostname": arg['<host>'], "rootpass": arg['<password>'] }]}
            headers = {'content-type': 'application/json'}
            r = requests.post(url, data=json.dumps(response), headers=headers)
            print r.text
        except  requests.ConnectionError:
            raise requests.ConnectionError
    @docopt_cmd
    def do_rm(self,arg):
        """Usage: rm <host>"""


    @docopt_cmd
    def do_list(self,arg):
        """Usage: list"""

    @docopt_cmd
    def do_deploy(self,arg):
        """Usage: deploy <packagename>"""


    @docopt_cmd
    def do_undeploy(self,arg):
        """Usage: undeploy <deployment-id>"""

    @docopt_cmd
    def do_user(self,arg):
        """Usage: user <host>"""


    @docopt_cmd
    def do_listsession(self,arg):
        """Usage: listsession"""


    def do_quit(self, arg):
        """Exit testgrid client"""
        exit()

opt = docopt(__doc__, sys.argv[1:])

if opt['start']:
    Command(opt['<host>'], opt['<port>'], opt['--username']).cmdloop()
    
print(opt)
