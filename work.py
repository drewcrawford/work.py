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
        print "  stop CASE_NO : Checks out of FogBugz case and checks into git Master branch"
    if (not command or command == "ship"):
        print "  ship : Closes case and pushes branch to origin"
    if (not command or command == "testmake"):
        print "  testmake CASE_NO : Makes a test subcase for CASE_NO"
    if (not command or command == "test"):
        print "  test CASE_NO : you are performing are reviewing/testing CASE_NO"
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
    
    #create new FogBugzConnect object to talk to FBAPI
    fbConnection = FogBugzConnect()
    
    #check for FogBugz case and clock in
    fbConnection.startCase(CASE_NO)
    
    #check for unsaved changes to source code
    gitConnection.checkForUnsavedChanges()
    
    #checkout or create branch with CASE_NO
    gitConnection.checkoutBranch(CASE_NO, fromSpec)
    
    print "Use work ship to commit your changes"

#
#
#
def projectStop(CASE_NO):
    #create new gitConnect object to talk to git
    gitConnection = GitConnect()
    
    #create new FogBugzConnect object to talk to FBAPI
    fbConnection = FogBugzConnect()
    
    #check for unsaved changes to source code
    gitConnection.checkForUnsavedChanges()
    
    #stop working on case and checkout master
    gitConnection.checkoutMaster()
    
    #clock out of project
    fbConnection.stopWork(CASE_NO)
    

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
    if("work-" in branch):
        caseNo = branch.split("-")[1]
        gitConnection.pushChangesToOriginBranch(branch)
        gitConnection.checkoutMaster()
        fbConnection.resolveCase(caseNo)
    else:
        print "ERROR: Not in correct working branch to ship!"
        quit()

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
    
    gitConnection = GitConnect()
    gitConnection.checkForUnsavedChanges()
    gitConnection.fetch()
    gitConnection.checkoutExistingBranch(parent)
    gitConnection.pull()
    
    fbConnection.startCase(test)
    
    
    

################################################################################
########################### Begin Script Here ##################################
################################################################################
#
# Check for command line arguments. give usage if none exists
#
task = ""
CASE_NO = 0
fromSpec = ""

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
    projectStop(CASE_NO)
elif(task == "ship"):
    projectShip()
elif (task == "testmake"):
    projectTestMake(CASE_NO)
elif (task == "test"):
    projectStartTest(CASE_NO)
else:
    printUsageString()



