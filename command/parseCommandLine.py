import argparse
import parseCommandString
from parseCommandString import *



class parseCommand:
    def __init__(self, funcMap):
        self.parser = argparse.ArgumentParser()
        self.subparsers = self.parser.add_subparsers(help=helpDescription.COMMAND)
        self.parserMap = {}
        self.setParser(funcMap, commandName.LIST, helpDescription.LIST)
        self.setParserWithArg(funcMap, commandName.ADD, helpDescription.ADD, helpArgDescription.ADD, argName.HOSTNAME, parserAttributes.NARGS)
        self.setParserWithArg(funcMap, commandName.RM, helpDescription.RM, helpArgDescription.RM, argName.HOSTNAME, parserAttributes.NARGS)

    def setParser(self, funcMap, comName, helpDescription):
        self.parserMap[comName] = self.subparsers.add_parser(comName, help=helpDescription)
        self.parserMap[comName].set_defaults(which=comName, func=funcMap[comName])

    def setParserWithArg(self, funcMap, comName, helpDescription, helpArgDescription,argName, nbArg):
        self.setParser(funcMap, comName, helpDescription)
        self.parserMap[comName].add_argument(argName, help=helpArgDescription, nargs=nbArg)


    def execParser(self, arg):
        args = self.parser.parse_args(arg)
        args.func(args)

