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
import os
import json

PURGATORY_STMT = "Through no fault of the Enrichment Center, you have managed to trap yourself in this room."


try:
    from magic import magic
except:
    class Dummy(): pass
    magic = Dummy()
    magic.SETTINGSFILE = os.path.expanduser("~/.workScript")
    magic.BUILDBOT_IXPERSON=7

try:
    import lint
    lint_loaded = True
except ImportError:
    lint_loaded = False

def get_setting_dict():
        try:
            handle = open(magic.SETTINGSFILE, "r")
            result = json.load(handle)
            handle.close()
            return result

        except:
            return {}
            
def set_setting_dict(dict):
        handle = open(magic.SETTINGSFILE, "w")
        json.dump(dict,handle,indent=2)
        handle.close()


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
    print "  integratemake MILESTONE --from=FROMSPEC: create a new integration branch\n\tfor the milestone (off of FROMSPEC)"
    print "  network : it's a series of tubes"
    print "  recharge FROM_CASE TO_CASE : Moves time charged against one case to be charged against another instead"
    print "  chargeback CASE : Prints total hours, including hours that were been recharged away somewhere else"
    print "  ls: list cases (EXPERIMENTAL)"
    print "  selftest: runs the tests (POOR TEST COVERAGE)"
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
    
    settings = get_setting_dict()
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
    if lint_loaded:
        try:
            result = lint.Lint.analyze()
        except:
            print sys.exc_info()
            print "Lint sunk the ship, but we still have a liferaft!"
        else:
            if not result:
                while True:
                    cont = raw_input("You're code failed lint analyses. Continue anyway? (Y/n)")
                    if cont == "n":
                        exit()
                    if cont == "Y":
                        break

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

    #create the pull request
    gitHubConnect = GitHubConnect()

    if not gitHubConnect.pullRequestAlreadyExists("work-%d" % caseno):
        body = "Ticket at %s/default.asp?%d\n%s" % (fbConnection.getFBURL(),caseno,raw_input("Type a note: "))
        list =  gitConnection.getUserRepo()
        integrationBranch = fbConnection.getIntegrationBranch(caseno)
        if integrationBranch=="Undecided":
            raise Exception("Come on now, you've implemented the ticket before you decided what mielstone it was?  You have to decide!")
        pullURL = gitHubConnect.createPullRequest("work-%d" % caseno,body,integrationBranch,"work-%d" % caseno)
        fbConnection.commentOn(caseno,"Pull request at %s\n%s" %(pullURL,body))


    #is there a test case?
    try:
        (parent,child) = fbConnection.getCaseTuple(caseno)
        fbConnection.resolveCase(caseno,isTestCase_CASENO=child)
    except:
        fbConnection.resolveCase(caseno)
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
    #get estimate
    print "Please provide an estimate for the test: ",
    est = raw_input()
    fbConnection.createTestCase(PARENT_CASE,estimate=est)
    

#
#   Automatically creates a test case for a case, if it does not already exist.
#   You may want to check the bug type before calling this method.
def autoTestMake(CASE_NO,fbConnection=None):
    print "autotestmake", CASE_NO
    if not fbConnection: fbConnection = FogBugzConnect()
    (implement,test)  = fbConnection.getCaseTuple(CASE_NO,oldTestCasesOK=True,exceptOnFailure=False)
    if not test:
        ixTester = fbConnection.optimalIxTester(CASE_NO)
        fbConnection.createTestCase(CASE_NO,ixTester=ixTester)
        return True
    return False

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
    gitHubConnection = GitHubConnect()
    gitHubConnection.openPullRequestByName("work-%d" % CASE_NO)


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
        purgatory = False
    else:
        purgatory = True



    caseno = gitConnection.extractCaseFromBranch()
    gitConnection.pushChangesToOriginBranch(gitConnection.getBranch())
    gitConnection.checkoutMaster()

    fbConnection = FogBugzConnect()
    (parent,test) = fbConnection.getCaseTuple(caseno)
    if purgatory: fbConnection.commentOn(parent,PURGATORY_STMT) #this signals buildbot to fail the case back to the implementer after PURGATORY expires
    #buildbot special-cases Inspect passes to be in PURGATORY, so no signaling is required for the pass case
    
    fbConnection.fbConnection.assign(ixBug=parent,ixPersonAssignedTo=magic.BUILDBOT_IXPERSON,sEvent="Terribly sorry but your case FAILED a test: %s" % reason)
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
    
    fbConnection.fbConnection.assign(ixBug=parent,ixPersonAssignedTo=magic.BUILDBOT_IXPERSON)

    # play sounds!
    getstatusoutput("afplay -v 7 %s/media/longcheer.aiff" % sys.prefix)

    #fbConnection.closeCase(parent)

#
#
#
def projectIntegrate(CASE_NO,defaultgitConnection=GitConnect()):
    if not defaultgitConnection:
        interactive = True
    else:
        interactive = False
    gitConnection = defaultgitConnection
    
    
    gitConnection.checkForUnsavedChanges()

    fbConnection = FogBugzConnect()
#still open here
    # make sure integration is even worth it...
    fbConnection.ensureReadyForTest(CASE_NO)


    gitConnection.checkoutExistingBranch(CASE_NO)
    
    integrate_to = fbConnection.getIntegrationBranch(CASE_NO)
    gitConnection.checkoutExistingBranchRaw(integrate_to)
    
    gitHubConnection = GitHubConnect()
    gitHubConnection.closePullRequestbyName("work-%d" % CASE_NO)
    #check for test case
    try:
        (parent, test) = fbConnection.getCaseTuple(CASE_NO,oldTestCasesOK=True)
    except:
            if interactive:
                print "WARNING: no test case! Press enter to continue"
                raw_input()
                
    if not interactive:
        if not gitConnection.mergeIn("work-%d" % CASE_NO,pretend=True):
            return False
    gitConnection.mergeIn("work-%d" % CASE_NO)

    fbConnection.commentOn(CASE_NO,"Merged into %s" % integrate_to)
    fbConnection.closeCase(CASE_NO)
    if not interactive:
        gitConnection.pushChangesToOriginBranch(branch=integrate_to)
    return True



#
#
#
def projectIntegrateMake(CASE_NO,fromSpec):
    if not fromSpec:
        print "Sorry, you have to manually specify a fromspec.  Ask somebody."
        quit()
    gitConnection = GitConnect()
    gitConnection.createNewRawBranch(CASE_NO,fromSpec)



def complain(ixComplainAboutPerson):
    fbConnection = FogBugzConnect()
    response = fbConnection.fbConnection.search(q="status:active assignedto:=%d" % ixComplainAboutPerson,cols="hrsCurrEst,hrsElapsed,sPersonAssignedTo,sFixFor")
    for case in response.cases:
        #print case
        if case.hrscurrest.contents[0]=="0":
            print "%s's case %s has no estimate" % (case.spersonassignedto.contents[0], case["ixbug"])
            fbConnection.commentOn(case["ixbug"],"This next test could take a very, VERY long time.")
        if case.sfixfor.contents[0]=="Undecided":
            print "%s needs a milestone" % case["ixbug"]
            fbConnection.commentOn(case["ixbug"],"If you choose not to decide, you still have made a choice.  (Don't think about it, don't think about it...)  It's a paradox!  There IS no answer.")
        est = float(case.hrscurrest.contents[0])
        act = float(case.hrselapsed.contents[0])
        if est - act < 0:
            print "%s's case %s requires updated estimate" % (case.spersonassignedto.contents[0], case["ixbug"])
            fbConnection.commentOn(case["ixbug"],"I'll give you credit:  I guess you ARE listening to me.  But for the record:  You don't have to go THAT slowly.")
        

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
    import dateutil.parser
    fbConnection = FogBugzConnect()
    fbConnection.setParentIfUnset(fr,to)
    #cannot create a time record for a closed case...
    mustOpen = not fbConnection.isOpen(to)
    if mustOpen:
        fbConnection.reopen(to,"work.py recharge")
    results = fbConnection.listTimeRecords(fr)
    time_interval = 0
    my_records = []
    for record in results:
        #print record
        if record.fdeleted.contents[0]!="false":
            print "Skipping deleted record %s" % record
            continue
        if len(record.dtend)==0:
            print "Skipping open time record %s" % record
            continue
        my_records.append(record)
    r = 0
    for record in my_records:
        print "%d: %s-%s" % (r,record.dtstart.contents[0],record.dtend.contents[0])
        r += 1
        
    def parse_range(astr): # http://stackoverflow.com/questions/4726168/parsing-command-line-input-for-numbers
        result=set()
        for part in astr.split(','):
            x=part.split('-')
            result.update(range(int(x[0]),int(x[-1])+1))
        return sorted(result)
        
    strl = raw_input("records  (syntax like 22-27,51-64): ")
    results = parse_range(strl)
    for result in results:
        record = my_records[result]
        record_desc = "From %s to %s ixPerson %s ixBug %s" % (record.dtstart.contents[0],record.dtend.contents[0],record.ixperson.contents[0],record.ixbug.contents[0])
        from_time = dateutil.parser.parse(record.dtstart.contents[0])
        to_time = dateutil.parser.parse(record.dtend.contents[0])
        time_interval += (to_time-from_time).seconds
        print from_time,to_time,time_interval

        fbConnection.commentOn(fr,"recharge: A record was removed from this ticket: %s, see case %d" % (record_desc,to))
        fbConnection.commentOn(to,"recharge: A record was added to this ticket: %s, see case %d" % (record_desc, fr))
        fbConnection.createTimeRecord(to,str(record.dtstart.contents[0]),str(record.dtend.contents[0]))
    oldEst = fbConnection.getEstimate(fr) * 60.0 * 60.0
    newEst = (oldEst - time_interval) / 60.0 / 60.0
    if newEst <= 0: newEst = 1/60.0
    print "Setting estimate to",newEst
    fbConnection.setEstimate(fr,timespan="%f hours" % newEst)
#fbConnection.deleteTimeRecord(record.ixinterval.contents[0])
    if mustOpen: fbConnection.closeCase(to)


#
#
#
def chargeback(case):
    import re
    fbConnection = FogBugzConnect()
    events = fbConnection.allEvents(case)
    total_time = 0
    
    def parsecase(match):
        if match:
            (fromt,tot) = match.groups(0)
            import dateutil.parser
            fromd = dateutil.parser.parse(fromt)
            tod = dateutil.parser.parse(tot)
            return (tod - fromd).seconds
        return 0
    for event in events:
        match = re.match("recharge: A record was removed from this ticket: From (.*) to (.*)(?=ixPerson)",event)
        total_time += parsecase(match)
        
        match = re.match("recharge: A record was added to this ticket: From (.*) to (.*)(?=ixPerson)",event)

        total_time -= parsecase(match)
        
    total_time += fbConnection.getElapsed(case) * 60.0 * 60.0
    (pcase,test) = fbConnection.getCaseTuple(case,oldTestCasesOK=True,exceptOnFailure=False)
    if test:
        total_time += fbConnection.getElapsed(test) * 60.0 * 60.0
    print total_time / 60.0 / 60.0, "hours"
    return total_time / 60.0 / 60.0


#sets a reasonable completion date per the EBS estimate for the milestone
def _fixFors_to_EBS_dates():
    print "--------SETTING DATES PER EBS-----------"
    fbConnection = FogBugzConnect()
    fixfors = fbConnection.dependencyOrder(fbConnection.listFixFors())
    
    for item in fixfors:
        name = fbConnection.nameForFixFor(fbConnection.fixForDetail(item))
        if name.startswith("Never"): continue
        print "processing",name,item
        date = fbConnection.getShipDate(item)
        from dateutil.parser import parse
        fbConnection.editFixForShipDate(item,parse(date))
    
#sets each test milestone to be one day following the appropriate release milestone.
def _fixFors_test_quickly_dates():
    print "--------FIXING TEST MILESTONES-----------"
    fbConnection = FogBugzConnect()
    fixfors_raw = fbConnection.listFixFors()
    fixfors = fbConnection.dependencyOrder(fixfors_raw)
    from dateutil.parser import parse
    import datetime
    #print fixfors
    for testMilestone in fixfors:
        
        testMilestone_raw = fbConnection.fixForDetail(testMilestone)
        testName = fbConnection.nameForFixFor(testMilestone_raw)
        if testName.startswith("Never"): continue
        print "processing",testMilestone,testName
        if not testName.endswith("-test"): continue
        if testName=="Undecided-test": continue
        matched = False
        if testMilestone_raw.ixproject.contents==[]: continue
        for item in fbConnection.listFixFors(ixProject=int(testMilestone_raw.ixproject.contents[0])):
            #print testName[:-5],fbConnection.nameForFixFor(item)
            if item.sfixfor.contents[0]==testName[:-5]:
                #print "matching",testName,fbConnection.nameForFixFor(item)
                matched = True
                break
        if not matched:
            print testMilestone_raw
            raise Exception("Cannot match "+testName)
        if item.dt.contents==[]:
            print "Can't set",testName," because the non-test milestone has no completion date."
            continue
        date = item.dt.contents[0]
        newDate = parse(date)+datetime.timedelta(hours=6) #turns out that using 1 day produces weird results.  If the next implementation milestone is completed within 24 hours, lots of weird things can happen
        print "setting",testName,"to",newDate
        fbConnection.editFixForShipDate(testMilestone,newDate)

def fixUp():
    _fixFors_to_EBS_dates()
    _fixFors_test_quickly_dates()


################################################################################
########################### Begin Script Here ##################################
################################################################################
#
# Check for command line arguments. give usage if none exists
#
import unittest

if __name__=="__main__":
    task = ""
    CASE_NO = 0
    fromSpec = ""

    #check for updates
    from urllib2 import urlopen
    version_no = urlopen("http://dl.dropbox.com/u/59605/work_autoupdate.txt").read()
    #########################
    WORK_PY_VERSION_NUMBER=23
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
    elif (task == "network"):
        network()
    elif (task == "recharge"):
        recharge(int(sys.argv[2]),int(sys.argv[3]))
    elif (task=="chargeback"):
        chargeback(int(sys.argv[2]))
    elif (task == "ls"):
        ls()
    elif (task == "config"):
        workConfig(target)
    elif (task=="selftest"):
        if len(sys.argv)>=3:
            suite = unittest.defaultTestLoader.loadTestsFromNames(["work.TestSequence."+sys.argv[2]])
        else:
            suite = unittest.defaultTestLoader.loadTestsFromNames(["work","gitHubConnect","fogbugzConnect"])
        unittest.TextTestRunner(failfast=True).run(suite)
    else:
        printUsageString()

class TestSequence(unittest.TestCase):
    def setUp(self):
        self.f = FogBugzConnect()
        pass

    def test_autotest(self):
        #print "HERE OMG"
        autoTestMake(2453)
        pass
        
    def test_fixup_fixfors(self):
        if not self.f.amIAdministrator():
            print "You can't run test_fixup_fixfors because you're not an administrator."
            return
        fixUp()
    
    def test_chargeback(self):
        f = FogBugzConnect()
        self.assertAlmostEqual(chargeback(1111),-5.123611111111112) #I'm not 100% sure that this test makes any sense
        
        #The sum of a set of tickets should be the same as the sum of the chargebacked tickets.
        #Note that chargeback adds up the test cases for us, but f.getElapsed does not
        self.assertAlmostEqual(chargeback(1997)+chargeback(2427)+chargeback(2431)+chargeback(2695),f.getElapsed(1997)+f.getElapsed(2427)+f.getElapsed(2431)+f.getElapsed(2695)+f.getElapsed(2186)+f.getElapsed(2521))
