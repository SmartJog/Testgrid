import argparse
import parseCommandString
from parseCommandString import *
import sys

class argHttp():
    def __init__(self, value=None, pwd=None):
        self.isAdmin = False
        self.rootPass = pwd
        self.commandLine = value

class ArgumentParserError(Exception): pass

class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)
        


class parseCommand():
    def __init__(self, funcMap):
        self.parser = ThrowingArgumentParser()
        self.subparsers = self.parser.add_subparsers(help=helpDescription.COMMAND)
        self.parserMap = {}
        self.setParser(funcMap, commandName.LIST, helpDescription.LIST, False)
        self.setParserWithArg(funcMap, commandName.ADD, helpDescription.ADD, helpArgDescription.ADD, argName.HOSTNAME, parserAttributes.NARGS, True)
        self.setParserWithArg(funcMap, commandName.RM, helpDescription.RM, helpArgDescription.RM, argName.HOSTNAME, parserAttributes.NARGS, True)

    def setParser(self, funcMap, comName, helpDescription, isAdmin):
        self.parserMap[comName] = self.subparsers.add_parser(comName, help=helpDescription)
        self.parserMap[comName].set_defaults(which=comName, func=funcMap[comName], admin=isAdmin, root=None)

    def setParserWithArg(self, funcMap, comName, helpDescription, helpArgDescription,argName, nbArg, isAdmin):
        self.setParser(funcMap, comName, helpDescription, isAdmin)
        self.parserMap[comName].add_argument(argName, help=helpArgDescription, nargs=nbArg)

    def  to_arg(self, arg_line):
        for arg in arg_line.split():
            if not arg.strip():
                continue
            yield arg

    def execParser(self, httpArg):
        try:
            args = self.parser.parse_args(self.to_arg(httpArg.commandLine))
            if httpArg.isAdmin == False and args.admin == True:
                result = "you must be admin to perform this operation"
                return result
            args.root = httpArg.rootPass
            result = args.func(args)
            return result
        except ArgumentParserError as e:
            return str(e)



