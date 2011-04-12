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
    if (not command or command == "view"):
        print "  view CASE_NO : Shows you CASE_NO"
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
    if (not command or command == "complain"):
        print "  complain:  finds and complains about late cases"
    if (not command or command == "integratemake"):
        print "  integratemake MILESTONE --from=FROMSPEC: create a new integration branch for the milestone (off of FROMSPEC)"
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
        
    #create new FogBugzConnect object to talk to FBAPI
    fbConnection = FogBugzConnect()
    
    #check for test case - should not run for test case
    if fbConnection.isTestCase(CASE_NO):
        print "ERROR: cannot start on test case! (did you mean \"work test\"?)"
        quit()
    
    #check for FogBugz case and clock in
    fbConnection.startCase(CASE_NO)
    

    
    if not fromSpec:
        #try to fill automatically from FB
        fromSpec = fbConnection.getIntegrationBranch(CASE_NO)
        print "using integration branch %s" % fromSpec
    #checkout or create branch with CASE_NO
    gitConnection.checkoutBranch(CASE_NO, fromSpec)
    
    fbConnection.view(CASE_NO)
    
    print "Use work ship to commit your changes"

#
#
#
def projectStop():
    #create new gitConnect object to talk to git
    gitConnection = GitConnect()
    
    #check for unsaved changes to source code
    gitConnection.checkForUnsavedChanges()
    
    #create new FogBugzConnect object to talk to FBAPI
    fbConnection = FogBugzConnect()
    
    caseno = gitConnection.extractCaseFromBranch()
    

    
    #stop working on case and checkout master
    branch = gitConnection.getBranch()
    gitConnection.pushChangesToOriginBranch(branch)
    gitConnection.checkoutMaster()
    
    #clock out of project
    fbConnection.stopWork(caseno)
    
#
#
#
def projectView(CASE_NO):
    fbConnection = FogBugzConnect()
    fbConnection.view(CASE_NO)
    

#
#
#
def projectShip():
    #create new gitConnect object to talk to git
    gitConnection = GitConnect()
    gitConnection.checkForUnsavedChanges();
    
    #create new FogBugzConnect object to talk to FBAPI
    fbConnection = FogBugzConnect()

    #check if we're in a git repo
    branch = gitConnection.getBranch();

    
    # check if branch is the right branch
    caseno = gitConnection.extractCaseFromBranch()
    gitConnection.pushChangesToOriginBranch(branch)
    gitConnection.checkoutMaster()
    
    #is there a test case?
    try:
        (parent,child) = fbConnection.getCaseTuple(caseno)
        fbConnection.resolveCase(caseno,isTestCase_CASENO=child)
    except:    
        fbConnection.resolveCase(caseno)

#
#
#
def projectTestMake(PARENT_CASE):
    #create new FogBugzConnect object to talk to FBAPI
    fbConnection = FogBugzConnect()
    fbConnection.createTestCase(PARENT_CASE)
    
def projectStartTest(CASE_NO):
    gitConnection = GitConnect()
    gitConnection.checkForUnsavedChanges()
    
    fbConnection = FogBugzConnect()
    
    #get the appropriate cases out of FogBugz
    (parent,test) = fbConnection.getCaseTuple(CASE_NO)
    fbConnection.ensureReadyForTest(parent)

    gitConnection.fetch()
    gitConnection.checkoutExistingBranch(parent)
    
    fbConnection.startCase(test)
    gitConnection.githubCompareView(fbConnection.getIntegrationBranch(parent),"work-%d" % parent)
    
    
#
#
#
def projectFailTest():
    gitConnection = GitConnect()
    gitConnection.checkForUnsavedChanges()
    
    reasons = {"0":"Failed a unit test.","1":"Failed a UI test"}
    for reason in reasons.keys():
        print reason," ",reasons[reason]
    print "Or just type why it failed."
    reason = raw_input()
    if reason in reasons.keys():
        reason = reasons[reason]
    
    

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
    
    # make sure integration is even worth it...
    fbConnection.ensureReadyForTest(CASE_NO)
    
    gitConnection.checkoutExistingBranch(CASE_NO)
    
    integrate_to = fbConnection.getIntegrationBranch(CASE_NO)
    
    gitConnection.checkoutExistingBranchRaw(integrate_to)
    gitConnection.pull()
    
    gitConnection.mergeIn("work-%d" % CASE_NO)
    
    fbConnection.commentOn(CASE_NO,"Merged into %s" % integrate_to)
    fbConnection.closeCase(CASE_NO)
    
    
#
#
#
def projectIntegrateMake(CASE_NO,fromSpec):
     gitConnection = GitConnect()
     gitConnection.createNewRawBranch(CASE_NO,fromSpec)

#
#
#
def complain():
    fbConnection = FogBugzConnect()
    fbConnection.fbConnection.setCurrentFilter(sFilter=10) #Active Cases
    response = fbConnection.fbConnection.search(cols="hrsCurrEst")
    for case in response.cases:
        #print case
        if case.hrscurrest.contents[0]=="0":
            print "case %s has no estimate"%case["ixbug"]
            fbConnection.commentOn(case["ixbug"],"work.py complain:  This case needs an estimate.")
    response = fbConnection.fbConnection.search(cols="hrsCurrEst,hrsElapsed")
    for case in response.cases:
        #print case
        
        est = float(case.hrscurrest.contents[0])
        act = float(case.hrselapsed.contents[0])
        if est - act < 0:
            print "case %s requires updated estimate"%case["ixbug"]
            fbConnection.commentOn(case["ixbug"],"work.py complain:  This case is 'out of time' and needs an updated estimate.")

    
    
    
    

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
WORK_PY_VERSION_NUMBER=10
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
            target = sys.argv[2]
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
elif (task == "integratemake"):
    projectIntegrateMake(target,fromSpec)
elif (task == "test"):
    projectStartTest(CASE_NO)
elif (task == "fail"):
    projectFailTest()
elif (task == "pass"):
    projectPassTest()
elif (task == "integrate"):
    projectIntegrate(CASE_NO,fromSpec)
elif (task == "view"):
    projectView(CASE_NO)
elif (task == "complain"):
    complain()
else:
    printUsageString()



