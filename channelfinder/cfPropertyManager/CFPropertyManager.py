'''
SEE cf-property-manager.cfg for example configuration file
'''
from channelfinder import ChannelFinderClient
from channelfinder.util import ChannelUtil
from optparse import OptionParser
from getpass import getpass
import re
import time
import sys

global username, client, exclusion_expression, password, SERVICE_URL, quiet, verbose

quiet=False
test=False
verbose=False
CFG_PATH=''
DBL_PATH=''
dbllines = None
cfglines = None
expression_list = []
username = "cf-update" #Defaults reinforced inside mainRun()
password = "1234"
channel_list=[]
SERVICE_URL='https://localhost:8181/ChannelFinder'
client = None
exclusion_expression = ""


def test_mode():
    test=True;
    verbose=True;
    quiet=False;


def readDBL(path):
    '''
    reads and stores .dbl file for processing
    '''
    global dbllines
    dbllines = [line.strip() for line in open(path)]
    return dbllines


def readConfiguration(path):
    global exclusion_expression
    '''
    Reads configuration file and calls passes expressions to applyExpression to be run across the .dbl file

    SEE cf-property-manager.cfg for example configuration file:

    propertyName=RegularExpression
    IGNORE=RegularExpression   --Ignores any line with a successful search return.

    devName=[{][^:}][^:}]*
    devType=[:][^{]*?[:}](?!.*[{])
    IGNORE=.*WtrSkid.*
    '''
    global cfglines, expression_list, exclusion_expression
    cfglines = [line.strip().split("=",1) for line in open(path)]
    for properties in cfglines:
        if(verbose): print properties[0] + " = " + properties[1]
        if properties[0] == "IGNORE":
            print "IGNORE "+properties[1]
            exclusion_expression = re.compile(properties[1])
        else:
            if client.findProperty(properties[0]) != None:
                try:
                    expression = re.compile(properties[1])
                    expression_list.append([expression, properties[0]])
                except Exception as e:
                    print 'Failed to find the property',properties[0]
                    print 'CAUSE:',e.message
    return cfglines


def clean(str):
    '''
    Removes all : { and } from line to simplify regular expression syntax.
    '''
    return str.replace(":", "").replace("{", "").replace("}","")


def applyExpression():
    '''
    Applies the regular expression to each of the lines in the .dbl file, and calls updateProperty on each result.
    '''
    global exclusion_expression
    if(exclusion_expression==""):
        exclusion_expression="[^_]+"
    for channel_name in dbllines:
        prop_list = []
        if(exclusion_expression.search(channel_name)!=None):
            if verbose: print "EXCLUDE: "+channel_name
        else:

                for expression in expression_list:

                    result = expression[0].search(channel_name)

                    if result != None:
                        value = clean(result.group())
                        if(verbose):  print  "FOUND: "+value +" in "+ channel_name
                        if value != "":
                            prop_list.append({u'name' : expression[1], u'owner' : username, u'value' : value})
                        else:
                            if(verbose): print "MISSING IN " + line
                if verbose: print "UPDATE "+channel_name
                try:
                    client.update(channel = {u'name' : channel_name, u'owner':username,u'properties':prop_list })
                except Exception as e:
                    print 'Failed to update: '+channel_name+" \n--Cause:"+ e.message


def updateProperty(result, property_name,channel_name):
    '''
    Creates or updates properties defined in configuration file for any channel object passed.
    '''
    if(verbose): print "ADD "+result+" TO "+property_name+ " IN " +channel_name
    client.set(property={u'name':property_name, u'owner' : username, u'value':result},channelName=channel_name)


def addChannel(result, property_name, channel_name):
    '''
    Presently not used method for building a list of channels to be batch-updated.
    '''
    global channel_list
    if (verbose):print "ADD "+result+" TO "+property_name+ " IN " +channel_name
    #channel_list.append(Channel(name=channel_name, owner=username,properties=[Property(property_name,username,result)]))
    #ch = Channel(name=channel_name, owner=username,properties=[Property(property_name,username,result)])
    #client.update(channel = ch)

def getPassword(option, opt_str, value, parser):
    '''
    Simple method to prompt user for password
    '''
    parser.values.password = getpass()


def __getDefaultConfig(arg, value):
    '''
    Clean reception of command line configurations for default assignment.
    '''
    if value == None:
        try:
            return _conf.get('DEFAULT', arg)
        except:
            return None
    else:
        return value


def startClient():
    '''
    Initiates client using default values if none are changed.
    '''
    global client
    client= ChannelFinderClient(BaseURL=SERVICE_URL, username=username, password=password)


def main():
    usage = "usage: %prog [options] filename.dbl filename2.cfg"
    parser = OptionParser(usage=usage)
    parser.add_option('-s', '--service', \
                      action='store', type='string', dest='serviceURL', \
                      help='the service URL')
    parser.add_option('-u', '--username', \
                      action='store', type='string', dest='username', \
                      help='username')
    parser.add_option('-v', '--verbose', \
                      action='store_true', default=False, dest='verbose', \
                      help='displays additional run information')
    parser.add_option('-p', '--password', \
                      action='callback', callback=getPassword, \
                      dest='password', \
                      help='prompt user for password')
    opts, args = parser.parse_args()
    if len(args) == 0 or args == None:
        parser.error('Please specify a file')
    mainRun(opts, args)


def mainRun(opts, args):
    '''
    Collects values from command line flags, also sets default values.

    Preps for run and initiates.
    '''
    global username, password, SERVICE_URL, quiet, verbose
    username = __getDefaultConfig('username', opts.username)
    password = __getDefaultConfig('password', opts.password)
    SERVICE_URL = __getDefaultConfig('serviceURL', opts.serviceURL)
    verbose = __getDefaultConfig('verbose', opts.verbose)
    if username==None:
        username='cf-update' #CURRENT DEFAULT
    if password==None:
        password='1234'      #CURRENT DEFAULT
    if SERVICE_URL==None:
        SERVICE_URL='https://webdev.cs.nsls2.local:8181/ChannelFinder' #CURRENT DEFAULT
    startClient()
    run(args[0], args[1])


def run(dbl_path,cfg_path):
    '''
    Core functionality sequence.
    '''
    global DBL_PATH, CFG_PATH
    if (verbose): print dbl_path, cfg_path
    DBL_PATH=dbl_path
    CFG_PATH=cfg_path

    readDBL(DBL_PATH)
    readConfiguration(CFG_PATH)
    applyExpression()


'''
Initiates program main() run when not being imported. Initiates client for testing when imported.
'''
if __name__ == "__main__":
    try:
        main()
    except IOError as e:
        print "IOError: " + e.message
    else:
        startClient()




