#!/usr/bin/env python
from JucheLog.juchelog import juche
from fogbugzConnect import FogBugzConnect
from gitConnect import GitConnect
try:
    import keyring
except:
    juche.warning("Could not import keyring API")
    #raise Exception("stacktraceplease")

import urllib2
from urllib import quote
import json

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
        from work import get_setting_dict, set_setting_dict
        user = raw_input("GitHub Username:")
        settings = get_setting_dict()
        settings["githubuser"]=user
        set_setting_dict(settings)
    

    
    def login(self):
        from work import get_setting_dict
        settings = get_setting_dict()
        self.username = None
        if "githubuser" in settings: self.username = settings["githubuser"]
        if not self.username:
            self.setCredentials()
            self.username = get_setting_dict()["githubuser"]
        self.password = keyring.get_password("github",self.username)
        if not self.password:
            import getpass
            self.password = getpass.getpass("GitHub password:")
            keyring.set_password("github",self.username,self.password)
                
    def Request(self,url,data):
        b64_userpass = basic_auth(self.username, self.password)
        req =  urllib2.Request(url,data)
        req.add_header('Authorization', 'Basic %s' % b64_userpass)
        #uncomment this line for more debug
        #urllib2.install_opener(urllib2.build_opener(urllib2.HTTPSHandler(debuglevel=9)))
        return req

    
    def __init__(self,gitConnect=None):
        if not gitConnect: gitConnect=GitConnect()
        repouser =  gitConnect.getUserRepo()
        self.ghRepo = repouser[1]
        self.ghRepoUser = repouser[0]
        
        self.login()
        

        
        
    def pullRequestAlreadyExists(self,titleSearch):
        req = self.Request("https://api.github.com/repos/%s/%s/pulls?state=open" % (self.ghRepoUser,self.ghRepo),None)
        result = json.loads(urllib2.urlopen(req).read())
        for obj in result:
            if obj["title"]==titleSearch: return obj["html_url"]
        return None
    
    def openPullRequestByName(self,name):
        url = self.pullRequestAlreadyExists(name)
        from os import system
        system("open %s" % url)
        
    def closePullRequestbyName(self,name):
        #this is kind of a hack
        url = self.pullRequestAlreadyExists(name)
        if not url:
            juche.warning("There does not appear to be any such pull request %s" % name)
            return
        import re
        id = re.search("\d+$",url).group()
        data = json.dumps({"state":"closed"})
        req = self.Request("https://api.github.com/repos/%s/%s/pulls/%s" % (self.ghRepoUser,self.ghRepo,id),data)
        req.get_method = lambda: 'PATCH' #functional ftw
        response = urllib2.urlopen(req)

                
    #
    #   You probably want to call pullRequestAlreadyExists before doing this.
    #
    def createPullRequest(self,requestTitle,requestBody,fromHere,toHere):
        dict = {"title":requestTitle,"body":requestBody,"base":fromHere,"head":toHere}
        #print "https://api.github.com/repos/%s/%s/pulls" % (self.ghRepoUser,self.ghRepo)
        #print dict
        req = self.Request("https://api.github.com/repos/%s/%s/pulls" % (self.ghRepoUser,self.ghRepo),json.dumps(dict))
        try:
            response = urllib2.urlopen(req)
            return json.loads(response.read())["html_url"]
        except urllib2.HTTPError as e:
            juche.exception(e)
            juche.error(e.read())
            raise e
        

        
import unittest
class TestSequence(unittest.TestCase):
    def setUp(self):
        self.g = GitHubConnect()
    
    def test_pullreq(self):
        #self.g.createPullRequest("drewcrawford/work.py","My sample pull request","This is a body","master","work-2622")
        self.g.closePullRequestbyName("work-2390")
if __name__ == '__main__':
    unittest.main()
    
        