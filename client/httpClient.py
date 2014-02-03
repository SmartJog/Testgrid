"""
Usage:
   my_program start <host> <port> [--username=<login>]

Options:
    --username=<login>
"""
import json
import requests
import sys
import signal
import cmd
from docopt import docopt, DocoptExit


def signal_handler(signal, frame):
    print 'You pressed Ctrl+C!'
    exit(0)

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
        self.username = None
        self.check_start_param(username)
        self.intro = 'Welcome to testgrid client!'
        cmd.Cmd.__init__(self)

    def check_start_param(self, username):
        try:
            if username is not None:
                url = 'http://{0}:{1}/ping?session={2}'.format(self.host, self.port, username)
                r = requests.get(url)
                data = r.json()
                if not data['failure']:
                    self.prompt = username + " >"
                    self.username = username
                else:
                    print data["message"]
                    exit()                    
            else:
                url = 'http://{0}:{1}/ping'.format(self.host, self.port)
                r = requests.get(url)
                data = r.json()
                if not data["failure"]:
                    self.prompt = data["newLogin"] + " >"
                    self.username = data["newLogin"]
                    print "your login is %s" % data["newLogin"]
        except  (requests.ConnectionError,  ValueError, ) as e:
            raise e
        #LocationParseError
    

    @docopt_cmd
    def do_add(self, arg):
        """Usage: add <host> <password>"""
        try:
            url = 'http://{0}:{1}/add'.format(self.host, self.port)
            print arg['<host>']
            requestData = {"host": [{ "hostname": arg['<host>'], "rootpass": arg['<password>'] }]}
            headers = {'content-type': 'application/json'}
            r = requests.post(url, data=json.dumps(requestData), headers=headers)
            data = r.json()
            print data["message"]
        except  requests.ConnectionError:
            raise requests.ConnectionError
    @docopt_cmd
    def do_rm(self,arg):
        """Usage: rm <host>"""
        url = 'http://{0}:{1}/delete?{2}'.format(self.host, self.port, arg['<host>'])
        r = requests.get(url)
        data = r.json()
        if data["failure"]:
            print "%s has been removed".format(arg['<host>'])
        else:
            print "fail to remove %s".format(arg['<host>'])

    @docopt_cmd
    def do_list(self,arg):
        """Usage: list"""
        url = 'http://{0}:{1}/list'.format(self.host, self.port)


    @docopt_cmd
    def do_deploy(self,arg):
        """Usage: deploy <packagename> [--version=<version>]"""

        s = requests.Session()
        s.auth = (self.username, None)
        if arg['--version']:
            url = 'http://{0}:{1}/deploy?name={2}&version={3}'.format(self.host, self.port, arg['<packagename>'], arg['--version'])
        else:
            url = 'http://{0}:{1}/deploy?name={2}'.format(self.host, self.port, arg['<packagename>'])
        r = s.get(url)
        responseData = r.json()
        print responseData['message']

    @docopt_cmd
    def do_undeploy(self,arg):
        """Usage: undeploy <deployment-id>"""
        s = requests.Session()
        s.auth = (self.username, None)
        url = 'http://{0}:{1}/undeploy?id={2}'.format(self.host, self.port, arg['<deployment-id>'])
        r = s.get(url)
        data = r.json()
        if not data['failure']:
            print "deployment {0} is undeployed".format(arg['<deployment-id>'])
        else:
            print "fail to undeploy eployment {0}".format(arg['<deployment-id>'])

    @docopt_cmd
    def do_user(self,arg):
        """Usage: user <host>"""
        s = requests.Session()
        s.auth = (self.username, None)
        url = 'http://{0}:{1}/user?hostname={2}'.format(self.host, self.port, arg['<host>'])
        r = s.get(url)
        data = r.json()
        if not data['failure']:
            print "username : {0} password: {1} for host: {2}".format(data["username"], data["password"], arg['<host>'])
        else:
            print data['message']

    @docopt_cmd
    def do_listsession(self,arg):
        """Usage: listsession"""
        s = requests.Session()
        print self.username
        s.auth = (self.username, None)
        url = 'http://{0}:{1}/deploymentlist'.format(self.host, self.port)
        r = s.get(url)
        responseData = r.json()
        print "deployment-id\tpackageName\tversion\t\tip\t"
        for item  in responseData["deployment"]:
            print "{0}\t\t{1}\t\t{2}\t\t{3}".format(item['index'], item['packageName'], item['version'], item['host'])

    def do_quit(self, arg):
        """Exit testgrid client"""
        exit()



if __name__ == '__main__':
    opt = docopt(__doc__, sys.argv[1:])
    if opt['start']:
        signal.signal(signal.SIGINT, signal_handler)
        Command(opt['<host>'], opt['<port>'], opt['--username']).cmdloop()

