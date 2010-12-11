import os

try:
    import simplejson as json
except:
    import json
    
try:
    from fogbugz import FogBugz
except Exception as e:
    print "Could not import FogBugz API because: ", e
    
    quit()
from xml.dom.minidom import parseString

class FogBugzConnect:
    
    #
    # Store settings for email and username in home directory
    #
    def setCredentials(self):
        email = raw_input("email: ")
        username = raw_input("username: ")
        handle = open(self.SETTINGS, "w")
        try:
            settings = {"email": email, "username": username}
            json.dump(settings, handle, indent=2)
        except:
            handle.close()
        return
    
    #
    # Get settings from home directory
    #
    def getCredentials(self, email = None, username = None):
        if email is not None and username is not None:
            return {"email": email, "username": username}
        if not os.path.exists(self.SETTINGS):
            self.setCredentials()
        handle = open(self.SETTINGS)
        try:
            return json.load(handle)
        finally:
            handle.close()
    
    #
    # log into fogbugz
    #
    def login(self):
        self.email = self.getCredentials()['email']
        self.username = self.getCredentials()['username']
        password = ""
        while True:
            if not password:
                import getpass
                password = getpass.getpass("FogBugz password: ")
            else:
                break
                
        #connect to fogbugz with fbapi and login
        self.fbConnection.logon(self.email, password)
        
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
    # extract txt from xml node
    #
    def getText(node):
        return ''.join(node.data)
    
    #
    # create a test case
    #
    def createTestCase(self,PARENT_CASE):
        print "How long does it take to test? ",
        timespan = raw_input()
        response = self.fbConnection.new(ixBugParent=PARENT_CASE,sTitle="Review",ixPersonAssignedTo=self.username,hrsCurrEst=timespan,sEvent="work.py automatically created this test case")
        print "Created case %s" % response.case['ixbug']
        
        
    #
    # Start work on a case
    #
    def startCase(self, CASE_NO):
        query = 'assignedto:"{0}" {1}'.format(self.username, CASE_NO)
        resp=self.fbConnection.search(q=query)
        if (resp):
            self.fbConnection.startWork(ixBug=CASE_NO)
        else:
            print "ERROR: FogBugz case does not exist or isn't assigned to you!!"
            quit()
        return
    
    #
    # Stop work
    #
    def stopWork(self, CASE_NO):
        query = 'assignedto:"{0}" {1}'.format(self.username, CASE_NO)
        resp=self.fbConnection.search(q=query)
        if (resp):
            self.fbConnection.stopWork()
        else:
            print "ERROR: FogBugz case does not exist or isn't assigned to you!"
        return
    
    #
    # resolve case with CASE_NO
    #
    def resolveCase(self, CASE_NO):
        query = 'assignedto:"{0}" {1}'.format(self.username, CASE_NO)
        resp=self.fbConnection.search(q=query)
        if(resp):
            self.fbConnection.resolve(ixBug=CASE_NO)
        else:
            print "ERROR: FogBugz case does not exists or isn't assigned to you!"
        return

    #
    # FogBugzConnect constructor!
    #
    def __init__(self):
        self.SETTINGS = os.path.expanduser("~/.workScript")
        self.email = ""
        self.username = ""
        self.fbConnection = FogBugz('http://drewcrawfordapps.fogbugz.com/')
        while True:
            try:
                self.login()
                break
            except:
                print "Wrong Password! Try again!"
    
    
    
    
