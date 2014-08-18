#copyright (c) 2014 arkena, released under the GPL license.

#####################
# 3rd-party modules #
#####################

import installsystems
import vagrant
import bottle
import docopt
import strfmt

#####################
# internal plumbing #
#####################

# inclusion order is important here

import model

import parser # model
import debian # model
import remote # model

import client # model, parser
import database # model, parser

import persistent # model, database

#import vgadapter # model, persistent, vagrant
#import isadapter # model, persistent, installsystems


###########
# clients #
###########

import local # client, *.Grid, *.Node
import rest # client
import inventory
