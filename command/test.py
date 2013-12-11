#!/usr/bin/python
import sys
import json
import ansible.runner

def test():
    results = ansible.runner.Runner(
        pattern='192.168.0.191', forks=10,
        module_name='apt', module_args='name=sqlite3 state=installed',timeout=10, remote_user='sbideaux', sudo_pass='sj20131112', sudo=True).run()
    if results is None:
        print "No hosts found"
        sys.exit(1)

    for (hostname, result) in results['contacted'].items():
        if not 'failed' in result:
            print "sucess ??????????????" #%s >>> %s" % (hostname, result['stdout'])

    for (hostname, result) in results['dark'].items():
        print "%s >>> %s" % (hostname, result)

if __name__ == '__main__':
    test()
