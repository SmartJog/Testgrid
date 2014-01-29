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
        results = ansible.runner.Runner(forks=10,module_name=moduleName, 
                                        module_args=moduleArg ,timeout=10, 
                                        remote_user='root', pattern=hostname, 
                                        host_list=inv).run()
        
        if results is None:
            raise model.NoAvailableHost()
        for (hostname, result) in results['contacted'].items():
            if 'failed' in result:
                return result['msg']
            #if not 'failed' in result:
             #   return result['stdout']

    @staticmethod        
    def createNewNode(hostname, username, rootpass, publickey, privatekey):
        userpass = Command.generateNewPassword()
        encPass = crypt.crypt(userpass,"22")
        comArg = "name={0}  password={1} shell=/bin/bash update_password=always".format(username ,encPass)
        Command.runCommand(hostname, 'user',comArg) 
        newNode = impl.Node(hostname, 
                            rootpass, 
                            username, 
                            userpass, 
                            publickey, 
                            privatekey)
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
    def installPackage(hostname):pass
        


