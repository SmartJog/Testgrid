import model
import os
import sshOperation
import random
import ansible.runner
import impl
import string
import crypt

class Command(model.Command):

    @staticmethod        
    def generateNewPassword():
        characters = string.ascii_letters + string.digits
        password =  "".join(random.choice(characters) for x in range(random.randint(5, 8)))
        return password

    @staticmethod        
    def runCommand(hostname, moduleName, moduleArg):
        inv = [hostname]
        results = ansible.runner.Runner(module_name=moduleName, 
                                        module_args=moduleArg ,timeout=10, 
                                        remote_user='root', pattern=hostname, 
                                        host_list=inv).run()
        if results is None:
            raise model.NoAvailableHost()
        for (hostname, result) in results['contacted'].items():
            if 'failed' in result:
                return False
            return True
            #if not 'failed' in result:
             #   return result['stdout']
             #changed FIX

    @staticmethod        
    def createNewNode(hostname, username, rootpass, publickey, privatekey):
        userpass = Command.generateNewPassword()
        encPass = crypt.crypt(userpass,"22")
        comArg = "name={0}  password={1} shell=/bin/bash update_password=always".format(username ,encPass)
        Command.runCommand(hostname, 'user',comArg)
        os = Command.checkOS(hostname)
        newNode = impl.Node(hostname, 
                            rootpass, 
                            username, 
                            userpass, 
                            publickey, 
                            privatekey,
                            os)
       
        return newNode

    @staticmethod        
    def addNode(hostname, rootpass):
        serverkey = "{0}.ssh/testGridkey.pub".format(os.path.expanduser("~/"))
        keyPair = sshOperation.sshConnection.checkNewClient(hostname, "root" , rootpass, serverkey)
        if keyPair == None:
            return None
        newNode = Command.createNewNode(hostname ,"testUser", rootpass, keyPair.publicKey ,keyPair.privateKey)
        return newNode


    @staticmethod        
    def installPackage(hostname, packageName, packageVersion):
        if packageVersion is None:
            moduleArg = "pkg={0} state=present".format(packageName)
        else:
            moduleArg = "pkg={0}={1} state=present".format(packageName, packageVersion)
        return (Command.runCommand(hostname, "apt", moduleArg))

    @staticmethod
    def uninstallPackage(hostname, packageName, packageVersion):
        moduleArg = "pkg={0} state=absent force=yes".format(packageName)
        return Command.runCommand(hostname, "apt", moduleArg)

    @staticmethod
    def checkOS(hostname):
        osNames = ["ubuntu", "debian"]
        moduleArg = "uname -a"
        for name in osNames:
            inv = [hostname]
            results = ansible.runner.Runner(module_name='command', 
                                            module_args=moduleArg ,timeout=10, 
                                            remote_user='root', pattern=hostname, 
                                            host_list=inv).run()

            if results is None:
                raise model.NoAvailableHost()
            for (hostname, result) in results['contacted'].items():
                if not 'failed' in result:
                    if name in result['stdout'].lower():
                        return name
        return None
            
