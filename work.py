#!/usr/bin/python

#############################################
############# DrewCrawfordApps ##############
#############################################
# work.py
#
# bash script to automate the workflow surrounding
# checking in and out of git repositories of
# specific projects based on the bug number.
#############################################

import sys
from gitConnect import GitConnect
from fogbugzConnect import FogBugzConnect

#
# Prints the usage string for this script
#
def printUsageString(command = 0):
    print "usage: work /command/ [args]"
    print ""
    if (not command or command == "start"):
        print "  start CASE_NO [--from=FROMSPEC] : Checks into FogBugz and git branch"
    if (not command or command == "stop"):
        print "  stop : Checks out of FogBugz case and checks into git Master branch"
    if (not command or command == "ship"):
        print "  ship : Closes case and pushes branch to origin"
    if (not command or command == "testmake"):
        print "  testmake CASE_NO : Makes a test subcase for CASE_NO"
    if (not command or command == "test"):
        print "  test CASE_NO : you are performing are reviewing/testing CASE_NO"
    if (not command or command == "fail"):
        print "  fail : the case has failed to pass a test"
    if (not command or command == "pass"):
        print "  pass: the case has passed a test"
    if (not command or command == "integrate"):
        print "  integrate: integrate the case to somewhere"
    print ""
    sys.exit()

#
# This function starts the project
# Arguments are CASE_NO and optional fromSpec
#
# Task is to begin work on a specific FogBugz Case Number. If FogBugz doesn't
# have a CASE_NO listed, stop. If a git branch for CASE_NO exists, check it out
# and clock into FogBugz. If there is no branch, create a branch.
#
def projectStart(CASE_NO, fromSpec):
    """
    print "Case no: " + str(CASE_NO)
    print "from: " + fromSpec
    """
    #create new gitConnect object to talk to git
    gitConnection = GitConnect()
    
    #check for unsaved changes to source code
    gitConnection.checkForUnsavedChanges()
    
    gitConnection.fetch()
    
    #create new FogBugzConnect object to talk to FBAPI
    fbConnection = FogBugzConnect()
    
    #check for FogBugz case and clock in
    fbConnection.startCase(CASE_NO)
    

    
    if not fromSpec:
        #try to fill automatically from FB
        fromSpec = fbConnection.getIntegrationBranch(CASE_NO)
        
    #checkout or create branch with CASE_NO
    gitConnection.checkoutBranch(CASE_NO, fromSpec)
    
    print "Use work ship to commit your changes"

#
#
#
def projectStop():
    #create new gitConnect object to talk to git
    gitConnection = GitConnect()
    
    #create new FogBugzConnect object to talk to FBAPI
    fbConnection = FogBugzConnect()
    
    caseno = gitConnection.extractCaseFromBranch()
    
    #check for unsaved changes to source code
    gitConnection.checkForUnsavedChanges()
    
    #stop working on case and checkout master
    gitConnection.checkoutMaster()
    
    #clock out of project
    fbConnection.stopWork(caseno)
    

#
#
#
def projectShip():
    #create new gitConnect object to talk to git
    gitConnection = GitConnect()
    
    #create new FogBugzConnect object to talk to FBAPI
    fbConnection = FogBugzConnect()

    #check if we're in a git repo and changes are commited
    branch = gitConnection.getBranch();
    gitConnection.checkForUnsavedChanges();
    
    # check if branch is the right branch
    caseno = gitConnection.extractCaseFromBranch()
    gitConnection.pushChangesToOriginBranch(branch)
    gitConnection.checkoutMaster()
    fbConnection.resolveCase(caseno)

#
#
#
def projectTestMake(PARENT_CASE):
    #create new FogBugzConnect object to talk to FBAPI
    fbConnection = FogBugzConnect()
    fbConnection.createTestCase(PARENT_CASE)
    
def projectStartTest(CASE_NO):
    fbConnection = FogBugzConnect()
    
    #get the appropriate cases out of FogBugz
    (parent,test) = fbConnection.getCaseTuple(CASE_NO)
    fbConnection.ensureReadyForTest(parent)
    gitConnection = GitConnect()
    gitConnection.checkForUnsavedChanges()
    gitConnection.fetch()
    gitConnection.checkoutExistingBranch(parent)
    gitConnection.pull()
    
    fbConnection.startCase(test)
    gitConnection.githubCompareView(fbConnection.getIntegrationBranch(CASE_NO),"work-%d" % CASE_NO)
    
    
#
#
#
def projectFailTest():
    reasons = {"0":"Failed a unit test.","1":"Failed a UI test"}
    for reason in reasons.keys():
        print reason," ",reasons[reason]
    print "Or just type why it failed."
    reason = raw_input()
    if reason in reasons.keys():
        reason = reasons[reason]
    
    
    gitConnection = GitConnect()
    gitConnection.checkForUnsavedChanges()
    caseno = gitConnection.extractCaseFromBranch()
    gitConnection.pushChangesToOriginBranch(gitConnection.getBranch())
    gitConnection.checkoutMaster()
    
    fbConnection = FogBugzConnect()
    (parent,test) = fbConnection.getCaseTuple(caseno)
    fbConnection.reactivate(parent,fbConnection.findImplementer(caseno),"Terribly sorry, but your case FAILED a test: %s" % reason)
    fbConnection.stopWork(test)
    
#
#
#
def projectPassTest():
    gitConnection = GitConnect()
    gitConnection.checkForUnsavedChanges()
    caseno = gitConnection.extractCaseFromBranch()
    gitConnection.pushChangesToOriginBranch(gitConnection.getBranch())
    gitConnection.checkoutMaster()
    
    fbConnection = FogBugzConnect()
    (parent,test) = fbConnection.getCaseTuple(caseno)
    statuses = fbConnection.getStatuses(test)
    for i in range(0,len(statuses.keys())):
        print i,":  ",statuses[sorted(statuses.keys())[i]]
        
    print "Choose your adventure: ",
    choice = input()
    ix = sorted(statuses.keys())[choice]
    
    fbConnection.resolveCase(test,ixstatus=ix)
    fbConnection.closeCase(test)
    
    #fbConnection.closeCase(parent)
    
#
#
#
def projectIntegrate(CASE_NO):
    gitConnection = GitConnect()
    gitConnection.checkForUnsavedChanges()
    
    fbConnection = FogBugzConnect()
    integrate_to = fbConnection.getIntegrationBranch(CASE_NO)
    
    gitConnection.checkoutExistingBranchRaw(integrate_to)
    gitConnection.pull()
    
    gitConnection.mergeIn("work-%d" % CASE_NO)
    
    fbConnection.commentOn(CASE_NO,"Merged into %s" % integrate_to)
    fbConnection.closeCase(CASE_NO)
    
    
    

################################################################################
########################### Begin Script Here ##################################
################################################################################
#
# Check for command line arguments. give usage if none exists
#
task = ""
CASE_NO = 0
fromSpec = ""

#check for updates
from urllib2 import urlopen
version_no = urlopen("http://dl.dropbox.com/u/59605/work_autoupdate.txt").read()
#########################
WORK_PY_VERSION_NUMBER=0
#########################
import re
if re.search("(?<=WORK_PY_VERSION_NUMBER=)\d+",version_no).group(0) != str(WORK_PY_VERSION_NUMBER):
    print '\033[93m\033[43m','WARNING: WORK.PY IS OUT OF DATE...','\033[0m'
    


if len(sys.argv) > 1:       #if there's at least one argument...
    task = sys.argv[1];
    
    if len(sys.argv) > 2:   # if there's a second argument...
        try:
            CASE_NO = int(sys.argv[2])
        except:
            printUsageString()
    if len(sys.argv) > 3:   # if there's a third argument...
        try:
            fromSpec = str(sys.argv[3]).split("=")[1]
        except:
            printUsageString("start")
else:   # quit if no task
    printUsageString()

# check for which task to handle
# tasks are:
#   start
#   stop
#   ship
if(task == "start"):
    projectStart(CASE_NO, fromSpec)
elif(task == "stop"):
    projectStop()
elif(task == "ship"):
    projectShip()
elif (task == "testmake"):
    projectTestMake(CASE_NO)
elif (task == "test"):
    projectStartTest(CASE_NO)
elif (task == "fail"):
    projectFailTest()
elif (task == "pass"):
    projectPassTest()
elif (task == "integrate"):
    projectIntegrate(CASE_NO)
else:
    printUsageString()



