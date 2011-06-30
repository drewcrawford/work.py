import os

try:
    import simplejson as json
except:
    import json
    
try:
    import keyring
except:
    print "Could not import keyring API"
    quit()
    
try:
    from fogbugz import FogBugz
    from fogbugz import FogBugzAPIError
except Exception as e:
    print "Could not import FogBugz API because: ", e
    
    quit()
from xml.dom.minidom import parseString
FB_URL = 'http://drewcrawfordapps.fogbugz.com/'

class FogBugzConnect:
    
    #
    # Store settings for email and username in home directory
    #
    def setCredentials(self):
        email = raw_input("email: ")
        #username = raw_input("username: ")
        handle = open(self.SETTINGS, "w")
        try:
            settings = {"email": email}
            json.dump(settings, handle, indent=2)
        except:
            handle.close()
        return
    
    def listCases(self,projectName):
        query = 'project:"%s" assignedTo:"%s" status:active' % (projectName,self.username.lower())
        cols = "sTitle,ixPriority" #careful with adding things here.  It seems to be the case
        # that adding a field here requires the case to have that field.  Hence
        # the convoluted logic below to also grab cases with no estimate.
        cases = self.fbConnection.search(q= query,cols=cols + ",hrsCurrEst,hrsElapsed")
        cases = list(cases.cases)        

        addlcases = self.fbConnection.search(q=query,cols=cols)
        for addlcase in addlcases.cases:
            def searchforixbug(ixbugno):
                for case in cases:
                    if case["ixbug"]==ixbugno: return True
                return False
            #print addlcase
            if not searchforixbug(addlcase["ixbug"]):
                cases.append(addlcase)
            
        def mcmp(x,y):
            x_1 = int(x.ixpriority.contents[0])
            x_2 = int(y.ixpriority.contents[0])
            if x_1 < x_2: return -1
            if x_1 > x_2: return 1
            return 0
        cases.sort(cmp=mcmp)

        #print cases
        print "case".rjust(5),"title".ljust(55),"priority".rjust(6),"timeleft".rjust(8)
    
        for case in cases:
            print case["ixbug"].rjust(5),
            print case.stitle.contents[0].ljust(55),
            print case.ixpriority.contents[0].rjust(6),
            if case.hrscurrest.contents[0]=="0":
                print "?".rjust(8)
            else:
                print ("%.2f" % (float(case.hrscurrest.contents[0])-float(case.hrselapsed.contents[0]))).rjust(8)
            
    #
    # set other settings
    #
    def setSetting(self, setting, value):
        handle = open(self.SETTINGS)
        currentSettings = json.load(handle)
        handle.close()
        handle = open(self.SETTINGS, "w")
        try:
            currentSettings[setting] = value
            json.dump(currentSettings, handle, indent=2)
        except:
            handle.close()
        return
    
    #
    # Get settings from home directory
    #
    def getCredentials(self, email = None, username = None):
        if email is not None:
            return {"email": email}
        if not os.path.exists(self.SETTINGS):
            self.setCredentials()
        handle = open(self.SETTINGS)
        try:
            return json.load(handle)
        finally:
            handle.close()
    #
    # Shows you CASE_NO
    #
    def view(self,CASE_NO):
        from os import system
        system("open " + FB_URL + "default.asp?%d" % CASE_NO)
    
    #
    # log into fogbugz
    #
    def login(self):
        self.email = self.getCredentials()['email']
        #self.username = self.getCredentials()['username']
        password = keyring.get_password('fogbugz', self.username)
        if not password:
            while True:
                if not password:
                    import getpass
                    password = getpass.getpass("FogBugz password: ")
                else:
                    keyring.set_password('fogbugz', self.username, password)
                    break
                
        #connect to fogbugz with fbapi and login
        self.fbConnection.logon(self.email, password)
        
        #fix username
        for person in self.fbConnection.listPeople().people:
            if person.semail.contents[0]==self.email:
                self.username = person.sfullname.contents[0].encode('utf-8')
                #print self.username
        
    #
    # search for a FB case with CASE_NO
    #
    def searchForCase(self, CASE_NO):
        query = str(CASE_NO)
        resp = self.fbConnection.search(q=query)
        if (resp.findAll('case')):
            return resp.findAll('case')
        else:
            return None
    #
    # Attach a comment to a case
    #
    def commentOn(self,CASE_NO,msg):
        response = self.fbConnection.edit(ixBug=CASE_NO,sEvent=msg)
        
    #
    # Find implementor for a case
    #
    def findImplementer(self,CASE_NO):
        query = str(CASE_NO)
        resp = self.fbConnection.search(q=query,cols="events")
        case = resp.case
        for event in case.events:
            import re
            if len(event.s.contents)==0: continue
            #print "looking at %s" % event.s.contents[0]
            match = re.search("(?<=work.py: ).*(?= is implementing)",event.s.contents[0])
            if match:
                username = match.group(0)
                for person in self.fbConnection.listPeople().people:
                    #print "matching %s against %s" % (person,username)
                    #print '"%s" is not "%s"' % (person.sfullname.contents[0]), username)
                    if person.sfullname.contents[0]==username:
                        print "reassigning to ixperson %s" % person.ixperson.contents[0]
                        return person.ixperson.contents[0]
        raise Exception("No match")
                
    
    #
    # Get ixPerson for a given username or current username
    #
    def usernameToIXPerson(self):
        for person in self.fbConnection.listPeople().people:
            if person.sfullname.contents[0] == self.username:
                return person.ixperson.contents[0]
    
    #
    # Reactivate case
    #
    def reactivate(self,CASE_NO,assignTo,msg):
        try:
            response = self.fbConnection.reactivate(ixBug=CASE_NO,sEvent=msg,ixPersonAssignedTo=assignTo)
        except FogBugzAPIError as e:
            print "Unexpected condition [%s] Is case closed? Attempting to recover..." % e
            response = self.fbConnection.reopen(ixBug=CASE_NO,sEvent=msg,ixPersonAssignedTo=assignTo)
            print "Recovery was successful."
    #
    # create a test case
    #
    def createTestCase(self,PARENT_CASE):
        #get estimate
        print "Please provide an estimate for the test: ",
        timespan = raw_input()
        #extract parent info
        resp = self.fbConnection.search(q=PARENT_CASE,cols="ixProject,ixArea,ixFixFor,sFixFor")
        
        #look for a test milestone
        milestones = self.fbConnection.listFixFors(ixProject=resp.case.ixproject.contents[0])
        ixTestMilestone = 0
        foundTestMilestone = False
        for aMilestone in milestones.fixfors:
            #print aMilestone.sfixfor.contents[0], resp.case.sfixfor.contents[0] + "-test"
            if(aMilestone.sfixfor.contents[0].find(resp.case.sfixfor.contents[0] + "-test") != -1):
                foundTestMilestone = True
                ixTestMilestone = aMilestone.ixfixfor.contents[0]
        
        testMilestone = resp.case.sfixfor.contents[0] + "-test"
        #print "testMilestone: ", testMilestone
        #print "\nfoundTestMilestone: ", foundTestMilestone

        if not foundTestMilestone:
            ixTestMilestone = self.fbConnection.newFixFor(ixProject=resp.case.ixproject.contents[0], sFixFor=testMilestone, fAssignable="1")
            self.fbConnection.addFixForDependency(ixFixFor=ixTestMilestone, ixFixForDependsOn=resp.case.ixproject.contents[0])
            #print "creating new milestone and setting dependencies! New Milestone: ", ixTestMilestone.ixfixfor.contents[0]
            ixTestMilestone = ixTestMilestone.ixfixfor.contents[0]

        #print resp.case
        response = self.fbConnection.new(ixBugParent=PARENT_CASE,sTitle="Review",ixPersonAssignedTo=self.usernameToIXPerson(),hrsCurrEst=timespan,sEvent="work.py automatically created this test case",ixCategory=6,
                                         ixProject=resp.case.ixproject.contents[0],ixArea=resp.case.ixarea.contents[0],ixFixFor=ixTestMilestone)
        print "Created case %s" % response.case['ixbug']
    def __isTestCase(self,actual_beautiful_soup_caselist,oldTestCasesOK=False):
        """Requires a caselist with sTitle,events,fOpen as attributes"""
        for case in actual_beautiful_soup_caselist:
            #print "BEGIN CASE",case
            if not case.fopen: continue
            if case.fopen.contents[0]=="false" and not oldTestCasesOK:return False
            if case.stitle.contents[0]=="Review":
                for event in case.events:
                    if event.s.contents[0]=="work.py automatically created this test case":
                        return True
        return False           
        
    #
    # returns true iff CASE_NO is a work.py test case
    #
    def isTestCase(self,CASE_NO,oldTestCasesOK=False):
        response = self.fbConnection.search(q=CASE_NO,cols="sTitle,events,fOpen")
        return self.__isTestCase(response,oldTestCasesOK=oldTestCasesOK)

        #print response
    #
    # 
    #
    def ensureReadyForTest(self,CASE_NO):
        response = self.fbConnection.search(q=CASE_NO,cols="sStatus")
        if "Implemented" not in response.case.sstatus.contents[0] and "Fixed" not in response.case.sstatus.contents[0]:
            print "Case %d is not ready for test!  (resolved or implemented)" % CASE_NO
            quit()
        
        
    #
    # return (actual_case, test_case) given either one
    #
    def getCaseTuple(self,SOME_CASE,oldTestCasesOK=False):
        if self.isTestCase(SOME_CASE):
            response = self.fbConnection.search(q=SOME_CASE,cols="ixBugParent")
            return (int(response.case.ixbugparent.contents[0]),SOME_CASE)
            
        else: #parent case
            response = self.fbConnection.search(q=SOME_CASE,cols="ixBugChildren")
            for child in "".join(response.case.ixbugchildren).split(","):
                if self.isTestCase(child,oldTestCasesOK=oldTestCasesOK):
                    if child=="":
                        return (SOME_CASE,None)
                    return (SOME_CASE,int(child))
        raise Exception("Cannot find a test case for %d",SOME_CASE)
        
    #
    # start testing a given case
    #
    def startTest(self,SOME_CASE):
        (parent,test) = self.getCaseTuple(SOME_CASE)
        
        
        
    #
    # Start work on a case
    #
    def startCase(self, CASE_NO,enforceNoTestCases=True):
        query = 'assignedto:"{0}" case:"{1}"'.format(self.username.lower(), CASE_NO)
        
        cols = "fOpen,hrsCurrEst"
        if enforceNoTestCases:
            cols += ",events,sTitle"
        resp=self.fbConnection.search(q=query, cols=cols)
        if enforceNoTestCases and self.__isTestCase(resp):
            print "Can't 'work start' a test case (maybe you meant 'work test'?)"
        if (resp and resp.case):
            #print resp
            if resp.case.fopen.contents[0] != "true":
                print "FATAL ERROR: FogBugz case is closed"
                quit()
            if resp.case.hrscurrest.contents[0] != "0":
                self.fbConnection.startWork(ixBug=CASE_NO)
                self.commentOn(CASE_NO,"work.py: %s is implementing." % self.username)
            else:
                self.setEstimate(CASE_NO)
                self.startCase(CASE_NO)
        else:
            print "ERROR: FogBugz case does not exist or isn't assigned to you!!"
            quit()
        return
    
    #
    # Lists statuses for a given case
    #
    def getStatuses(self,CASE_NO):
        resp = self.fbConnection.search(q=CASE_NO,cols="ixCategory")
        category = resp.case.ixcategory.contents[0]
        resp = self.fbConnection.listStatuses(ixCategory=category)
        result = {}
        for status in resp.statuses:
            if status.fresolved.contents[0]=="false": continue
            result[status.ixstatus.contents[0]] = status.sstatus.contents[0]
        return result
    
    #
    # Stop work
    #
    def stopWork(self, CASE_NO):
        query = 'assignedto:"{0}" {1}'.format(self.username.lower(), CASE_NO)
        resp=self.fbConnection.search(q=query)
        if (resp):
            self.fbConnection.stopWork()
        else:
            print "ERROR: FogBugz case does not exist or isn't assigned to you!"
        return
    
    #
    #
    #
    def getIntegrationBranch(self,CASE_NO):
        resp = self.fbConnection.search(q=CASE_NO,cols="sFixFor")
        return (resp.case.sfixfor.contents[0].encode('utf-8'))
    
    #
    # resolve case with CASE_NO
    #
    def resolveCase(self, CASE_NO,ixstatus=None, isTestCase_CASENO=None):
        query = 'assignedto:"{0}" {1}'.format(self.username.lower(), CASE_NO)
        resp=self.fbConnection.search(q=query)
        if(resp):
            if (ixstatus):
                self.fbConnection.resolve(ixBug=CASE_NO,ixStatus=ixstatus)
            elif(isTestCase_CASENO):
                tester = self.findTestCaseOwner(isTestCase_CASENO)
                print "reassigning to ixperson",tester
                self.fbConnection.resolve(ixBug=CASE_NO,ixPersonAssignedTo=tester)
            else:
                self.fbConnection.resolve(ixBug=CASE_NO)

    
        else:
            print "ERROR: FogBugz case does not exists or isn't assigned to you!"
        return

    #
    #
    #
    def findTestCaseOwner(self, CASE_NO):
        query = '{0}'.format(CASE_NO)
        resp=self.fbConnection.search(q=query,cols="ixPersonAssignedTo")
        if(resp):
            tester = resp.case.ixpersonassignedto.contents[0]
            return tester
            
    
    #
    # close case with CASE_NO
    #
    def closeCase(self,CASE_NO):
        self.fbConnection.close(ixBug=CASE_NO)

    #
    # Set Estimate for specified bug, returns the estimate
    #
    def setEstimate(self, CASE_NO):
        print "Please provide an estimate for this case: ",
        timespan = raw_input()
        
        self.fbConnection.edit(ixBug=CASE_NO, hrsCurrEst=timespan)
        return timespan;


    #
    # FogBugzConnect constructor!
    #
    def __init__(self):
        self.SETTINGS = os.path.expanduser("~/.workScript")
        self.email = ""
        self.username = ""
        self.fbConnection = FogBugz(FB_URL)
        for i in range(0,1):
            if i == 3:
                print "Too many failed attempts! Sorry!"
                quit()
            try:
                self.login()
                break
            except:
                print "Wrong Password! Try again!"
    
    
    
    
