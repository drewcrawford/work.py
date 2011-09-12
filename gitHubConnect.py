#!/usr/bin/env python

from fogbugzConnect import FogBugzConnect
import json
try:
    import keyring
except:
    print "Could not import keyring API"
    quit()

import urllib2
from urllib import quote

import base64

def basic_auth(username, password):
    b64_userpass = base64.b64encode(
    '%s:%s' % (username, password))
    b64_userpass = b64_userpass.replace('\n', '')
    return b64_userpass
class GitHubConnect:
    
    
    #
    # Collects user settings
    #
    def setCredentials(self):
        user = raw_input("GitHub Username:")
        settings = FogBugzConnect.get_setting_dict()
        settings["githubuser"]=user
        FogBugzConnect.set_setting_dict(settings)
    

    
    def login(self):
        settings = FogBugzConnect.get_setting_dict()
        self.username = None
        if "githubuser" in settings: self.username = settings["githubuser"]
        if not self.username:
            self.setCredentials()
            self.username = FogBugzConnect.get_setting_dict()["githubuser"]
        self.password = keyring.get_password("github",self.username)
        if not self.password:
            import getpass
            self.password = getpass.getpass("GitHub password:")
            keyring.set_password("github",self.username,self.password)
    
    def Request(self,url,data):
        b64_userpass = basic_auth(self.username, self.password)
        req =  urllib2.Request(url,data)
        req.add_header('Authorization', 'Basic %s' % b64_userpass)
        return req

    
    def __init__(self):
        self.login()

        
        
    #
    #
    #
    def createPullRequest(self,projectMiniURI,requestTitle,requestBody,fromHere,toHere):
        dict = {"title":requestTitle,"body":requestBody,"base":fromHere,"head":toHere}
        print "https://api.github.com/repos/%s/pulls" % projectMiniURI
        print dict
        req = self.Request("https://api.github.com/repos/%s/pulls" % projectMiniURI,json.dumps(dict))
        response = urllib2.urlopen(req)
        return json.loads(response.read())["html_url"]
        

        
import unittest
class TestSequence(unittest.TestCase):
    def setUp(self):
        self.g = GitHubConnect()
    
    def test_pullreq(self):
        self.g.createPullRequest("drewcrawford/work.py","My sample pull request","This is a body","master","work-2622")
        
if __name__ == '__main__':
    unittest.main()
    
        