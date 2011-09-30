import os

try:
    import simplejson as json
except:
    import json


try:
    import keyring
except:
    print "Could not import keyring API"
    #raise Exception("stacktraceplease")



try:
    from fogbugz import FogBugz
    from fogbugz import FogBugzAPIError
except Exception as e:
    print "Could not import FogBugz API because: ", e

    #raise Exception("stacktraceplease")
from xml.dom.minidom import parseString

TEST_IXCATEGORY=6
class FogBugzConnect:


    """
    def prettify(self,fogbugzObj,omitTopLevel=False):
        Going forward, this is the recommended method to parse objects from BeautifulSoup.

        from BeautifulSoup import CData, NavigableString
        if omitTopLevel: return [self.prettify(child,omitTopLevel=False) for child in fogbugzObj]
        adict = {}
        done_something = False
        def append_or_someth(dict,key,obj):
            if not dict.has_key(key): dict[key]=obj
            elif isinstance(dict[key],list): dict[key].append(obj)
            else: dict[key] = [dict[key],obj]
        for k in fogbugzObj:
            if str(k).strip()=="": continue #schedule likes to insert random newlines
            if not hasattr(k,"name"):
                if isinstance(k,CData): 
                    assert(not done_something)
                    #print "fastreturn",k
                    return k.encode('utf-8')
                elif isinstance(k,NavigableString):
                    assert(not done_something)
                    #print "fastreturn",k
                    return k
                else:
                    print "unknown class",k.__class__
                    done_something = True
                    append_or_someth(adict,"other",str(k))
            else:
                done_something = True
                #print "push",k.name
                krepr = self.prettify(k.contents,omitTopLevel=False)
                append_or_someth(adict,k.name,krepr)
        #print "returning",adict
        return adict"""
    #
    #
    #

    def amIAdministrator(self):
        people = self.fbConnection.listPeople()
        for person in people.people:
            if int(person.ixperson.contents[0])==self.ixPerson:
                return person.fadministrator.contents[0]=="true"
        return False
    #
    # Store settings for email and username in home directory
    #
    def setCredentials(self):
        fburl = raw_input("FB URL [http://drewcrawfordapps.fogbugz.com/]: ")

        email = raw_input("email: ")
        from work import get_setting_dict, set_setting_dict
        settings = get_setting_dict()
        settings["email"]=email
        settings["fburl"] = fburl and fburl or "http://drewcrawfordapps.fogbugz.com/"
        set_setting_dict(settings)
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
    # get FB URL from settings
    #
    def getFBURL(self):
        from work import get_setting_dict
        settings = get_setting_dict()
        if "fburl" not in settings:
            self.setCredentials()
            settings = get_setting_dict()
        return settings["fburl"]


    #
    # Shows you CASE_NO
    #
    def view(self,CASE_NO):
        from os import system
        system("open " + self.getFBURL() + "default.asp?%d" % CASE_NO)

    #
    # log into fogbugz
    #
    def login(self):
        from work import get_setting_dict
        self.email = get_setting_dict()['email']
        #self.username = self.getCredentials()['username']
        if get_setting_dict().has_key('explicitFBToken'):
            self.fbConnection.logonTok(get_setting_dict()['explicitFBToken'])
        else:
            password = keyring.get_password('fogbugz', self.email)
            if not password:
                while True:
                    if not password:
                        import getpass
                        password = getpass.getpass("FogBugz password: ")
                    else:
                        keyring.set_password('fogbugz', self.email, password)
                        break

            #connect to fogbugz with fbapi and login
            self.fbConnection.logon(self.email, password)
        for person in self.fbConnection.listPeople().people:
            if person.semail.contents[0]==self.email:
                self.username = person.sfullname.contents[0].encode('utf-8')
        if not self.username:
            raise Exception("No username was found!")
        #print self.username
        self.ixPerson = self.usernameToIXPerson()
        #print self.ixPerson

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
        response = self.fbConnection.edit(ixBug=CASE_NO,sEvent=msg,ixPersonEditedBy=self.ixPerson)



    #
    # Find implementor for a case
    #
    def findImplementer(self,CASE_NO):
        query = str(CASE_NO)
        resp = self.fbConnection.search(q=query,cols="events,ixPersonAssignedTo")
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
                        #print "reassigning to ixperson %s" % person.ixperson.contents[0]
                        return int(person.ixperson.contents[0])
        #no match
        return int(case.ixpersonassignedto.contents[0])


    #
    # Get ixPerson for a given username or current username
    #
    def usernameToIXPerson(self):
        for person in self.fbConnection.listPeople(fIncludeVirtual=1,fIncludeNormal=1).people:
            if person.sfullname.contents[0] == self.username:
                return int(person.ixperson.contents[0])
        raise Exception("No such person!")

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
    # isOpen : determines if the case is open
    #
    def isOpen(self,CASE_NO):
        q = self.fbConnection.search(q=CASE_NO,cols="fOpen")
        return q.fopen.contents[0]!="false"

    # reopen : reopens case (not a reactivate... this auto-resolves the case)
    def reopen(self,CASE_NO,msg):
        q = self.fbConnection.search(q=CASE_NO,cols="ixStatus")
        #print q.ixstatus.contents[0]

        self.fbConnection.reopen(ixBug=CASE_NO,sEvent=msg)
        self.fbConnection.resolve(ixBug=CASE_NO,ixStatus=int(q.ixstatus.contents[0]),sEvent=msg)

    #
    #
    #
    def fixForDetail(self,ixFixFor):
        list = self.listFixFors()
        for fixfor in list:
            ix = int(fixfor.ixfixfor.contents[0])
            if ix==ixFixFor:
                return fixfor
        raise Exception("Unknown fixfor")

    #
    #
    #
    def nameForFixFor(self,ixFixForDetail):
        return ixFixForDetail.sfixfor.contents[0].encode('utf-8')



    #
    #
    #
    def getFixForDeleted(self,ixFixForDetail):
        return ixFixForDetail.fdeleted.contents[0]=="true"

    def getFixForStartDate(self,ixFixForDetail):
        if ixFixForDetail.dtstart.contents==[]:
            return "" #FogBugz API understands this string a lot better than None
        return ixFixForDetail.dtstart.contents[0]

    #
    #
    #
    def editFixForShipDate(self,ixFixFor,shipDate,depCheck=True):
        if depCheck:
            override = False
            deptree = self._deptree(self.listFixFors())
            from dateutil.parser import parse
            import datetime
            for dep in deptree[ixFixFor]:
                if dep not in deptree.keys(): continue
                depdetail = self.fixForDetail(dep)
                depdate = parse(depdetail.dt.contents[0])
                if depdate > shipDate:
                    override = True
                    shipDate = depdate + datetime.timedelta(hours=1)
            if override:
                print "Ship date overridden to ",shipDate
        detail = self.fixForDetail(ixFixFor)
        name = self.nameForFixFor(detail)
        print "editing ship date of",name
        self.fbConnection.editFixFor(ixFixFor=ixFixFor,sFixFor=name,dtRelease=shipDate,dtStart=self.getFixForStartDate(detail),fAssignable=self.getFixForDeleted(detail) and "0" or "1")

    #
    #
    #
    def getShipDate(self,ixFixFor,ixPriority=4):
        r = self.fbConnection.viewShipDateReport(ixFixFor=ixFixFor,ixPriority=ixPriority)
        array = list(r.shipdatereport.rgdt.array) #http://www.fogcreek.com/fogbugz/library/80/?topic=/fogbugz/library/80/html/2DCFC902.htm
        #print array
        count = len(array)
        return array[count/2].contents[0]
    #
    #
    #
    def getBurndown(self,ixFixFor,cumulativeHours=True,ixPriority=4):
        array = list (self.fbConnection.viewHoursRemainingReport(ixFixFor=ixFixFor,ixPriority=ixPriority,fThisFixForOnly=not cumulativeHours).rghr.array)
        count = len(array)
        return array[count/2].contents[0]

    #
    #
    #
    def listFixFors(self,ixProject=None):
        if ixProject:
            r = self.fbConnection.listFixFors(ixProject=ixProject).fixfors
        else:
            r = self.fbConnection.listFixFors().fixfors
        #print r
        return r

    def _deptree(self,fixFors):
        deptree = {} #key = ixFixFor, val = [ixDep1,ixDep2]
        for fixfor in fixFors:
            #print "processing ",int(fixfor.ixfixfor.contents[0])
            deps = []
            for dep in fixfor.setixfixfordependency:
                #print dep
                deps.append(int(dep.contents[0]))
            deptree[int(fixfor.ixfixfor.contents[0])]=deps
        return deptree

    #
    # Sorts the fixFors into an order with the independent milestones first.
    # FogBugz tends to complain if you mutate a milestone to be e.g. after its child.
    #
    def dependencyOrder(self,fixFors):
        deptree = self._deptree(fixFors)
        #print deptree
        cleared = []
        while True:
            for fixfor in deptree.keys():
                if fixfor in cleared: continue
                if len(deptree[fixfor])==0:
                    cleared.append(fixfor)
                    continue
                deps_cleared = True
                for dep in deptree[fixfor]:
                    if dep not in cleared and deptree.has_key(dep):
                        deps_cleared = False
                        break
                if deps_cleared:
                    cleared.append(fixfor)
                    continue
                else:
                    pass
                    #print "Can't add",fixfor,deptree[fixfor],"to list",cleared
            if len(cleared) == len(deptree):
                break
        return cleared



    #
    # Sets parent if not currently set
    #
    def setParentIfUnset(self,CASE_NO,toParent):
        q = self.fbConnection.search(q=CASE_NO,cols="ixBugParent")
        if q.ixbugparent.contents[0]=="0":
            self.fbConnection.edit(ixBug=CASE_NO,ixBugParent=toParent)

    def lookupIxArea(self,ixArea):
        resp = self.fbConnection.listAreas(ixArea=ixArea)
        for area in resp.areas:
            if area.ixarea.contents[0]==str(ixArea):
                return area
    def lookupIxProject(self,ixProject):
        resp = self.fbConnection.listProjects(ixProject = ixProject)
        for project in resp.projects:
            if project.ixproject.contents[0]==str(ixProject):
                return project

    #looks up the owner of the area, and failing that, the owner of the project
    def findCaseAreaixOwner(self,CASE_NO):
        resp = self.fbConnection.search(q=CASE_NO,cols="ixProject,ixArea")
        ixArea = int(resp.case.ixarea.contents[0])
        areaDetail = self.lookupIxArea(ixArea)
        if len(areaDetail.ixpersonowner.contents)!= 0:
            return int(areaDetail.ixpersonowner.contents[0])
        #look up project
        project = self.lookupIxProject(resp.case.ixproject.contents[0])
        return int(project.ixpersonowner.contents[0])

    #
    # finds an optimal tester for the case (ixperson)
    #
    def optimalIxTester(self,CASE_NO):
        from work import magic
        area_owner = self.findCaseAreaixOwner(CASE_NO)
        implementer = self.findImplementer(CASE_NO)
        if area_owner!= implementer:
            return area_owner
        #otherwise
        people = map(lambda x: int(x.ixperson.contents[0]),self.fbConnection.listPeople().people)
        people = filter(lambda x: x != magic.BUILDBOT_IXPERSON,people)
        people = filter(lambda x: x != implementer,people)
        from random import choice
        return choice(people)


    #
    # create a test case
    #
    def createTestCase(self,PARENT_CASE,estimate="0 hours",ixTester=None):
        if not ixTester:
            ixTester = self.ixPerson
        #extract parent info
        resp = self.fbConnection.search(q=PARENT_CASE,cols="ixProject,ixArea,ixFixFor,sFixFor,ixPriority")
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
            ixTestMilestone = self.fbConnection.newFixFor(ixProject=resp.case.ixproject.contents[0],sFixFor=testMilestone, fAssignable="1")
            self.fbConnection.addFixForDependency(ixFixFor=ixTestMilestone, ixFixForDependsOn=resp.case.ixproject.contents[0])
            #print "creating new milestone and setting dependencies! New Milestone: ", ixTestMilestone.ixfixfor.contents[0]
            ixTestMilestone = ixTestMilestone.ixfixfor.contents[0]

        #print resp.case
        response = self.fbConnection.new(ixBugParent=PARENT_CASE,sTitle="Review",ixPersonAssignedTo=ixTester,hrsCurrEst=estimate,ixPriority=resp.case.ixpriority.contents[0],sEvent="Cake and grief counseling will be available at the conclusion of the test.",ixCategory=6,
                                         ixProject=resp.case.ixproject.contents[0],ixArea=resp.case.ixarea.contents[0],ixFixFor=ixTestMilestone)
        print "Created case %s" % response.case['ixbug']
    def __isTestCase(self,actual_beautiful_soup_caselist,oldTestCasesOK=False):
        """Requires a caselist with sTitle,ixCategory,fOpen as attributes"""
        for case in actual_beautiful_soup_caselist:
            #print "BEGIN CASE",case
            if not case.fopen: continue
            if case.fopen.contents[0]=="false" and not oldTestCasesOK:return False
            if not case.stitle.contents[0]=="Review": return False
            if case.ixcategory.contents[0]==str(TEST_IXCATEGORY): return True
        return False

    def allEvents(self,CASE_NO):
        resp = self.fbConnection.search(q=CASE_NO,cols="events")
        case = resp.case
        events = []
        for event in case.events:
            if len(event.s.contents)==0: continue
            events.append(event.s.contents[0])
        return events

    #
    # returns true iff CASE_NO is a work.py test case
    #
    def isTestCase(self,CASE_NO,oldTestCasesOK=False):
        response = self.fbConnection.search(q=CASE_NO,cols="sTitle,ixCategory,fOpen")
        return self.__isTestCase(response,oldTestCasesOK=oldTestCasesOK)

        #print response
    #
    #
    #
    def ensureReadyForTest(self,CASE_NO):
            if not self.isReadyForTest(CASE_NO):
                print "Case %d is not ready for test!  (resolved or implemented)" % CASE_NO
                raise Exception("stacktraceplease")
            
    def isReadyForTest(self,CASE_NO):
        response = self.fbConnection.search(q=CASE_NO,cols="sStatus")
        if "Implemented" not in response.case.sstatus.contents[0] and "Fixed" not in response.case.sstatus.contents[0]:
            return False
        return True

    #
    #
    #
    def ixChildren(self,CASE_NO):
        response = self.fbConnection.search(q=CASE_NO,cols="ixBugChildren")
        children = []
        for child in "".join(response.case.ixbugchildren).split(","):
            if child == '': continue
            children.append(int(child))
        return children
    #
    # return (actual_case, test_case) given either one
    #
    def getCaseTuple(self,SOME_CASE,oldTestCasesOK=False,exceptOnFailure=True):
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

        if exceptOnFailure:
            raise Exception("Cannot find a test case for %d",SOME_CASE)
        else:
            return (SOME_CASE,None)

    #
    # start testing a given case
    #
    def startTest(self,SOME_CASE):
        (parent,test) = self.getCaseTuple(SOME_CASE)


    #
    # List time records for a case
    #
    def listTimeRecords(self,CASE_NO="",dateStart="",dateEnd="",ixPerson=None):
        if not ixPerson:
            ixPerson = self.ixPerson
        return list(self.fbConnection.listIntervals(ixPerson=ixPerson,ixBug=CASE_NO,dtStart=dateStart,dtEnd=dateEnd).intervals)

    def sumTimeRecords(self,prettyRecordList):
        secs = 0
        from dateutil.parser import parse
        for record in prettyRecordList:
            #print record
            start = parse(record.dtstart.string)
            if not record.dtend.contents: continue
            end = parse(record.dtend.string)
            secs += (end - start).seconds
        return secs

    def expectedWorkHours(self,ixPerson,date):
        import datetime
        from dateutil.tz import tzutc
        schedule = self.fbConnection.listWorkingSchedule(ixPerson=ixPerson)
        # http://support.fogcreek.com/default.asp?fogbugz.4.60277.3
        start = float(schedule.nworkdaystarts.string)
        end = float(schedule.nworkdayends.string)
        hours_worked =  abs(end - start)
        if start > end: hours_worked -= 24
        hours_worked = abs(hours_worked)
        if schedule.fhaslunch.string!="false":hours_worked -= float(schedule.hrslunchlength.string)
        days = ["sunday","monday","tuesday","wednesday","thursday","friday"]
        workdays = filter(lambda x: str(x).strip() != "",list(schedule.rgworkdays))
        #print workdays
        if workdays[date.weekday()].string=="true":
            return hours_worked
        else:
            return 0.0

        print hours_worked
        return schedule

    #
    # deleting time records
    # FB API has no support for this, so we're spoofing a web request...
    #
    def deleteTimeRecord(self,ixInterval,dt=None):
        #get the date for FB

        import urllib2, urllib
        import cookielib
        cj = cookielib.CookieJar()
        handler = urllib2.HTTPCookieProcessor(cj)
        #opener = urllib2.build_opener(urllib2.HTTPSHandler(debuglevel=1),handler) #uncomment for better debugging
        opener = urllib2.build_opener(handler)

        urllib2.install_opener(opener)
        BASE_URL = "https://drewcrawfordapps.fogbugz.com/" # we require HTTPS for this...
        password = keyring.get_password('fogbugz', "")
        if not password: raise Exception("no password")
        data = urllib.urlencode([("pre","preLogon"),("dest",""),("sPerson",self.email),("sPassword",password)])
        result = urllib2.urlopen(BASE_URL)
        result = urllib2.urlopen(BASE_URL+"default.asp?",data)
        #result = urllib2.urlopen(BASE_URL+"default.asp?fAlaCarte=1&pg=pgAlaCartePopupContent&fPgFavorites=0&fList=0&fPlatformChrome=0&sSearchString=&_=1312763516639")
        data = urllib.urlencode([("ixInterval",ixInterval),("pre","preDeleteInterval"),("dt",dt),("btnDelete","Yes")])
        result = urllib2.urlopen(BASE_URL+"default.asp",data)

    #
    # Create time records for a case
    #
    def createTimeRecord(self,CASE_NO,dtStart,dtEnd):
        self.fbConnection.newInterval(ixBug=CASE_NO,dtStart=dtStart,dtEnd=dtEnd)

    #
    # Start work on a case
    #
    def startCase(self, CASE_NO,enforceNoTestCases=True):
        query = 'assignedto:"{0}" case:"{1}"'.format(self.username.lower(), CASE_NO)

        cols = "fOpen,hrsCurrEst"
        if enforceNoTestCases:
            cols += ",ixCategory,sTitle"
        resp=self.fbConnection.search(q=query, cols=cols)
        if enforceNoTestCases and self.__isTestCase(resp):
            print "Can't 'work start' a test case (maybe you meant 'work test'?)"
            return
        if (resp and resp.case):
            #print resp
            if resp.case.fopen.contents[0] != "true":
                print "FATAL ERROR: FogBugz case is closed"
                raise Exception("stacktraceplease")
            if resp.case.hrscurrest.contents[0] != "0":
                self.fbConnection.startWork(ixBug=CASE_NO,enforceNoTestCases=enforceNoTestCases)
                self.commentOn(CASE_NO,"work.py: %s is implementing." % self.username)
            else:
                self.setEstimate(CASE_NO)
                self.startCase(CASE_NO)
        else:
            print "ERROR: FogBugz case does not exist or isn't assigned to you!!"
            raise Exception("stacktraceplease")
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

    #returns the time the user was last active, if any.
    #If the user has not been active "lately", for some definition of lately, may return none.
    def userLastActive(self,ixPerson):
        import datetime
        resp = self.fbConnection.listIntervals(ixPerson=ixPerson,dtStart=datetime.datetime.now() - datetime.timedelta(days=2))
        from dateutil.parser import parse
        last = datetime.datetime.min
        from dateutil import tz
        class UTC(datetime.tzinfo):
            """UTC"""

            def utcoffset(self, dt):
               return datetime.timedelta(0)

            def tzname(self, dt):
               return "UTC"

            def dst(self, dt):
                return datetime.timedelta(0)

        last = last.replace(tzinfo=UTC())
        for interval in resp.intervals:
            if len(interval.dtend)==0: return datetime.datetime.now().replace(tzinfo=tz.tzlocal()) + datetime.timedelta(seconds=-30) #annoyableIxPeople depends on this function returning a time less than the current time.
            date = parse(interval.dtend.contents[0])
            if date > last: last = date
        if last == datetime.datetime.min.replace(tzinfo=UTC()): return None
        return last

    #
    # returns a list of annoyable ixPeople
    #
    def annoyableIxPeople(self):
        from dateutil import tz
        annoyable = []
        people = self.fbConnection.listPeople()
        import datetime
        for person in people.people:
            ix = int(person.ixperson.contents[0])
            referencetime = datetime.datetime.now().replace(hour=12,minute=0,second=0,tzinfo=tz.gettz(name="CST"))
            nowtime = datetime.datetime.now().replace(tzinfo=tz.tzlocal())
            #print referencetime
            #print nowtime
            if nowtime > referencetime:
                delta =  (nowtime - referencetime).seconds
            else:
                delta =  (referencetime-nowtime).seconds
            if delta / 60.0 / 60.0 < 1.0: #within an hour of the prescribed time
                annoyable.append(ix)
            else:
                lastActive = self.userLastActive(ix)
                if not lastActive:
                    print "User",ix,"does not appear to be active recently"
                    continue

                delta = (nowtime - lastActive).seconds
                if delta / 60.0 / 60.0 < 1.0: #within an hour of the prescribed time
                    annoyable.append(ix)
        return annoyable

    #
    # resolve case with CASE_NO
    #
    def resolveCase(self, CASE_NO,ixstatus=None, isTestCase_CASENO=None):
        query = 'assignedto:"{0}" {1}'.format(self.username.lower(), CASE_NO)
        resp=self.fbConnection.search(q=query)
        if(resp):
            if (ixstatus):
                self.fbConnection.resolve(ixBug=CASE_NO,ixStatus=ixstatus)
            else:
                self.fbConnection.resolve(ixBug=CASE_NO,ixPersonAssignedTo=7)


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
    # Returns the elapsed time (hours)
    #
    def getElapsed(self,CASE_NO):
        resp = self.fbConnection.search(q=str(CASE_NO),cols="hrsElapsed")
        return float(resp.case.hrselapsed.contents[0])


    #
    # Returns current estimate (hours)
    #
    def getEstimate(self,CASE_NO):
        resp = self.fbConnection.search(q=str(CASE_NO),cols="hrsCurrEst")
        return float(resp.case.hrscurrest.contents[0])
    #
    # Set Estimate for specified bug, returns the estimate
    #
    def setEstimate(self, CASE_NO,timespan=None):
        if not timespan:
            print "Please provide an estimate for this case: ",
            timespan = raw_input()

        self.fbConnection.edit(ixBug=CASE_NO, hrsCurrEst=timespan)
        return timespan;


    #
    # FogBugzConnect constructor!
    #
    def __init__(self):
        self.email = ""
        self.username = ""
        self.fbConnection = FogBugz(self.getFBURL())
        self.login()

import unittest


class TestSequence(unittest.TestCase):
    def setUp(self):
        self.f = FogBugzConnect()
    
    def test_aa_fileupload(self):
        self.f.fbConnection.edit(ixBug=3178,sEvent="test upload event",files={"filename1.txt":"Contents of filename1","filename2.txt":"Contents of filename2"})

    def test_ixBugChildren(self):
        self.assertTrue(len(self.f.ixChildren(2525))==1)
        self.assertTrue(self.f.ixChildren(407)==[2978])
        
    def test_setestimate(self):
        self.f.setEstimate(3262,timespan="0.0586111111111 hours")
        self.assertAlmostEqual(self.f.getEstimate(3262),0.06)

    def test_annoyables(self):
        if not self.f.amIAdministrator():
            print "WARNING: NOT RUNNING test_annoyables BECAUSE YOU ARE NOT AN ADMINISTRATOR"
            return
        print self.f.annoyableIxPeople()

    def test_optimaltester(self):
        print self.f.optimalIxTester(3028)

    def test_events(self):
        self.assertTrue(self.f.allEvents(2525) >= 3)

    def test_testcase(self):
        #self.f.createTestCase(3000)
        pass

    def test_lastactive(self):
        print self.f.userLastActive(self.f.ixPerson)

    def test_deptree(self):
        print self.f.dependencyOrder(self.f.listFixFors())

    def test_getship(self):
        print self.f.getShipDate(ixFixFor=43)

    def test_admin(self):
        print "I am an administrator:",self.f.amIAdministrator()

    def test_burndown(self):
        print self.f.getBurndown(ixFixFor=43)

    def test_listtimerecords(self):
        records = self.f.listTimeRecords(1111)
        self.assertEqual(len(records),1)
        self.assertEqual(self.f.sumTimeRecords(records),26)

    def test_workingschedule(self):
        import datetime
        print "Drew works %f hours" % self.f.expectedWorkHours(ixPerson=2,date=datetime.datetime.now())


if __name__ == '__main__':
    unittest.main(failfast=True)
