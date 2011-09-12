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
from commands import getstatusoutput
from gitConnect import GitConnect
from fogbugzConnect import FogBugzConnect
from gitHubConnect import GitHubConnect

#
# Prints the usage string for this script
#
def printUsageString():
    print "usage: work /command/ [args]"
    print ""
    print "  config [setting]=[value] : adds setting to work.py config file"
    print "  view CASE_NO : Shows you CASE_NO"
    print "  start CASE_NO [--from=FROMSPEC] : Checks into FogBugz and git branch"
    print "  stop : Checks out of FogBugz case and checks into git Master branch"
    print "  ship : Closes case and pushes branch to origin"
    print "  testmake CASE_NO : Makes a test subcase for CASE_NO"
    print "  test CASE_NO : you are performing are reviewing/testing CASE_NO"
    print "  fail : the case has failed to pass a test"
    print "  pass: the case has passed a test"
    print "  integrate: integrate the case to somewhere"
    print "  complain:  finds and complains about late cases"
    print "  integratemake MILESTONE --from=FROMSPEC: create a new integration branch\n\tfor the milestone (off of FROMSPEC)"
    print "  network : it's a series of tubes"
    print "  recharge FROM_CASE TO_CASE : Moves time charged against one case to be charged against another instead"
    print "  ls: list cases (EXPERIMENTAL)"
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
        
    #check for FogBugz case and clock in
    fbConnection.startCase(CASE_NO)

    

    #checkout or create branch with CASE_NO
    gitConnection.checkoutBranch(CASE_NO,fromSpec,fbConnection)
    
    settings = fbConnection.getSettings()
    if not "viewOnStart" in settings or settings["viewOnStart"] == 1:
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
    #gitConnection.checkoutMaster()

    #create the pull request
    gitHubConnect = GitHubConnect()
    body = raw_input("Type a note: ")
    list =  gitConnection.getUserRepo()
    (user,repo) = list[0],list[1]
    pullURL = gitHubConnect.createPullRequest("%s/%s" % (user,repo),"work-%d" % caseno,body,fbConnection.getIntegrationBranch(caseno),"work-%d" % caseno)
    fbConnection.commentOn(caseno,"Pull request at %s\n%s" %(pullURL,body))
    
    
    #is there a test case?
    try:
        (parent,child) = fbConnection.getCaseTuple(caseno)
        #fbConnection.resolveCase(caseno,isTestCase_CASENO=child)
    except:
        #fbConnection.resolveCase(caseno)
        pass
    print """There's about an 80% chance that whatever you just did was work that rightfully belongs to some other (possibly closed) case.  Recharging is a way to signify to EBS that your work should be counted against a different case.
        
        Ex 1: You're fixing a somewhat-forseeable bug in a feature that was implemented and estimated in another case, but for some reason a new bug has been filed instead of the old feature reactivated.  Recharge to the original feature, as whoever estimated that should have accounted for a relatively bug-free implementation.
        
        Ex 2: You're implementing a feature that was originally estimated in some other case.  Maybe it was a parent case that was broken down into child cases, or maybe somebody carved out a feature of a larger something for you to implement.
        
        When there are multiple candidates for a recharge, use your judgment.  Pick the newer case where reasonable.
        
        DO NOT RECHARGE
        1) Things that are legitimately and substantially new features
        2) Test cases, inquiries, or fake tickets
        3) Build feedback / ship tickets """

    print "recharge to: (case#)",
    TO_CASE = raw_input()
    if TO_CASE:
        to = int(TO_CASE)
        recharge(caseno,to)



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
    
    fbConnection.startCase(test,enforceNoTestCases=False)
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

    # play sounds!
    getstatusoutput ("afplay -v 7 %s/media/dundundun.aiff" % sys.prefix)
    
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

    # play sounds!
    getstatusoutput("afplay -v 7 %s/media/longcheer.aiff" % sys.prefix)
    
    #fbConnection.closeCase(parent)

#
#
#
def projectIntegrate(CASE_NO):
    gitConnection = GitConnect()
    gitConnection.checkForUnsavedChanges()

    fbConnection = FogBugzConnect()
#still open here 
    # make sure integration is even worth it...
    fbConnection.ensureReadyForTest(CASE_NO)
    gitConnection.checkoutExistingBranch(CASE_NO)
    integrate_to = fbConnection.getIntegrationBranch(CASE_NO)
    
    #check for test case
    try:
        (parent, test) = fbConnection.getCaseTuple(CASE_NO,oldTestCasesOK=True)
    except:
            print "WARNING: no test case! Press enter to continue"
            raw_input()
        
    
    gitConnection.checkoutExistingBranchRaw(integrate_to)
    gitConnection.pull()

    gitConnection.mergeIn("work-%d" % CASE_NO)

    fbConnection.commentOn(CASE_NO,"Merged into %s" % integrate_to)
    fbConnection.closeCase(CASE_NO)


#
#
#
def projectIntegrateMake(CASE_NO,fromSpec):
    if not fromSpec:
        print "Sorry, you have to manually specify a fromspec.  Ask somebody."
        quit()
    gitConnection = GitConnect()
    gitConnection.createNewRawBranch(CASE_NO,fromSpec)

#
#
#
def complain():
    fbConnection = FogBugzConnect()
    fbConnection.fbConnection.setCurrentFilter(sFilter=10) #Active Cases
    response = fbConnection.fbConnection.search(cols="hrsCurrEst,sPersonAssignedTo")
    for case in response.cases:
        #print case
        if case.hrscurrest.contents[0]=="0":
            print "%s's case %s has no estimate" % (case.spersonassignedto.contents[0], case["ixbug"])
            fbConnection.commentOn(case["ixbug"],"work.py complain:  This case needs an estimate.")
    response = fbConnection.fbConnection.search(cols="hrsCurrEst,hrsElapsed,sPersonAssignedTo")
    for case in response.cases:
        #print case

        est = float(case.hrscurrest.contents[0])
        act = float(case.hrselapsed.contents[0])
        if est - act < 0:
            print "%s's case %s requires updated estimate" % (case.spersonassignedto.contents[0], case["ixbug"])
            fbConnection.commentOn(case["ixbug"],"work.py complain:  This case is 'out of time' and needs an updated estimate.")

#
# Work.py config. Allows user to create/set a setting and insert it into
# the settings file. Displays a warning if not in a list of non-standard
# settings.
#
def workConfig(settingString):
    ALLOWED_SETTINGS = ["viewOnStart"]
    if len(settingString.split("=")) < 2:
        printUsageString()
        quit()
    
    setting = settingString.split("=")[0]
    value = settingString.split("=")[1]
    if setting and value:
        fbConnection = FogBugzConnect()
        settings = fbConnection.getCredentials()
        if(not setting in ALLOWED_SETTINGS):
            print "WARNING: setting not known. Will be added anyway."
        fbConnection.setSetting(setting, value)
    else:
        printUsageString()
        quit()
        
#
#
#
def network():
    gitConnection = GitConnect()
    gitConnection.githubNetwork()
    
#
#
#
def ls():
    gitConnection = GitConnect()
    (user,repo) = gitConnection.getUserRepo()
    fbConnection = FogBugzConnect()
    if repo=="DrewCrawfordApps": repo = "Hackity-Hack"
    elif repo=="Briefcase-wars": repo = "Briefcase Wars"
    fbConnection.listCases(repo)

#
#
#
def recharge(fr,to):
    fbConnection = FogBugzConnect()
    fbConnection.setParentIfUnset(fr,to)
    #cannot create a time record for a closed case...
    mustOpen = not fbConnection.isOpen(to)
    if mustOpen:
        fbConnection.reopen(to,"work.py recharge")
    results = fbConnection.listTimeRecords(fr)
    
    for record in results:
        print record
        if record.fdeleted.contents[0]!="false":
            print "Skipping deleted record %s" % record
            continue
        if len(record.dtend)==0:
            print "Skipping open time record %s" % record
            continue
        
        record_desc = "From %s to %s ixPerson %s ixBug %s" % (record.dtstart.contents[0],record.dtend.contents[0],record.ixperson.contents[0],record.ixbug.contents[0])
#print to,record.dtstart.contents[0],record.dtend.contents[0]
        fbConnection.commentOn(fr,"recharge: A record was removed from this ticket: %s, see case %d" % (record_desc,to))
        fbConnection.commentOn(to,"recharge: A record was added to this ticket: %s, see case %d" % (record_desc, fr))
        fbConnection.createTimeRecord(to,str(record.dtstart.contents[0]),str(record.dtend.contents[0]))
#fbConnection.deleteTimeRecord(record.ixinterval.contents[0])
    if mustOpen: fbConnection.closeCase(to)


    





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
WORK_PY_VERSION_NUMBER=22
#########################
import re
if re.search("(?<=WORK_PY_VERSION_NUMBER=)\d+",version_no).group(0) != str(WORK_PY_VERSION_NUMBER):
    from gitConnect import bcolors
    print bcolors.WARNING,'WARNING: WORK.PY IS OUT OF DATE...',bcolors.ENDC
    


#Attention: Older methods in here used to have a fixed argument format (1 = case, 2 = from=case).
#However, with the plethora of new work commands this assumption is somewhat broken.
#Going forward, we should do the parsing for the command in its elif block rather than up here
#todo: refactor existing stuff

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
            fromSpec = fromSpec.replace(" ","-")
        except:
            pass
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
    if not CASE_NO:
        printUsageString()
    projectTestMake(CASE_NO)
elif (task == "integratemake"):
    projectIntegrateMake(target.replace(" ","-"),fromSpec)
elif (task == "test"):
    projectStartTest(CASE_NO)
elif (task == "fail"):
    projectFailTest()
elif (task == "pass"):
    projectPassTest()
elif (task == "integrate"):
    projectIntegrate(CASE_NO)
elif (task == "view"):
    projectView(CASE_NO)
elif (task == "complain"):
    complain()
elif (task == "network"):
    network()
elif (task == "recharge"):
    recharge(int(sys.argv[2]),int(sys.argv[3]))
elif (task == "ls"):
    ls()
elif (task == "config"):
    workConfig(target)
else:
    printUsageString()
