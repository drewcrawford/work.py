from subprocess import Popen, PIPE
import os
import sys
from commands import getstatusoutput
import commands
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[43m\033[1;34m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    
def WARN(str):
    print bcolors.WARNING + str + bcolors.ENDC
    

class GitConnect:
    #
    # Checks to see if we're in a Git Repo
    #
    def checkForRepository(self):
        (status, output) = commands.getstatusoutput("git status")
        if(status):
            print "ERROR: Not in git repository! Check your current directory!"
            quit()
        else: 
            return output
        
        
    #
    # Return (user,repo) for current working copy
    #
    def getUserRepo(self):
        (status,output) = commands.getstatusoutput("git remote show origin")
        import re
        userRepo = re.search("(?<=Fetch URL: git@github.com:).*",output).group(0).split("/")
        userRepo[1] = userRepo[1].replace(".git","")
        return userRepo
        

    #
    # Launch gitHub compare view
    #   
    def githubCompareView(self,origin,dest):
        (user,repo) = self.getUserRepo()
        cmd =  "http://github.com/%s/%s/compare/%s...%s" % (user,repo,origin,dest)
        from os import system
        system("open %s" % cmd)
    #
    # Shows the network
    #
    def githubNetwork(self):
        (user,repo) = self.getUserRepo()
        cmd = "http://github.com/%s/%s/network" % (user,repo)
        from os import system
        system("open %s" % cmd)
    
    #
    # Returns the branch, else quits
    #
    def getBranch(self):
        output = self.checkForRepository()
        output = output.split("\n")[0].split(" ")[3]
        return output
    
    #
    #
    #
    def extractCaseFromBranch(self):
        branch = self.getBranch()
        if("work-" in branch):
            return int(branch.split("-")[1])
        else:
            raise Exception("Branch %s is not a work branch!" % branch)
    #
    # Performs a git fetch
    #
    def fetch(self):
        self.checkForRepository()
        (status,output) = commands.getstatusoutput("git fetch")
        if status:
            print "ERROR:  Cannot fetch! %s" % output
            quit()
            
    def __mergeInPretend(self,BRANCH_NAME): #http://stackoverflow.com/questions/501407/is-there-a-git-merge-dry-run-option/6283843#6283843
        (status,ancestor) = self.statusOutput("git merge-base %s %s" % (BRANCH_NAME,self.getBranch()))
        if status:
            raise Exception("Unexpected error while pretending %d %s" % (status,ancestor))
        print "a",ancestor
        print "b",self.getBranch()
        (status,output) = self.statusOutput("git merge-tree %s %s %s" % (ancestor,BRANCH_NAME,self.getBranch()))
        print status, output
    #
    #
    #
    def mergeIn(self,BRANCH_NAME,pretend=False):
        if pretend:
            return self.__mergeInPretend(BRANCH_NAME)
        print "Merging in %s..." % BRANCH_NAME
        (status,output) = commands.getstatusoutput("git merge --no-ff %s" % BRANCH_NAME)
        print output
        if status:
            print "ERROR: merge was unsuccessful."
            # play sounds!
            getstatusoutput ("afplay -v 7 %s/media/ohno.aiff" % sys.prefix)
            quit()
        else:
            # play sounds!
            getstatusoutput ("afplay -v 7 %s/media/hooray.aiff" % sys.prefix)
        print "Use 'git push' to ship."
    
    #
    # Performs a git pull
    #
    def pull(self):
        self.checkForRepository()
        import ConfigParser
        c = ConfigParser.ConfigParser()
        path = ".git/config"
        import os
        for i in range(0,30):
            if os.path.exists(path): break
            path = "../" + path
            if i==30:
                raise Exception("Not a git repository?")
        
        file = open(path)
        str = file.read()
        file.close()

        print "Pulling...",
        if self.getBranch() not in str:
            WARN( "WARNING: %s is not a tracking branch." % self.getBranch())
            print "Attempting to fix...",
            try:
                self.setUpstream(self.getBranch(),"remotes/origin/{0}".format(self.getBranch()))
                print "Success!"
            except:
                print "ERROR: DID NOT AUTOMATICALLY FIX BRANCH UPSTREAM / TRACKING.  PLEASE FILE A BUG."

            (status,output) = commands.getstatusoutput("git pull origin %s" % self.getBranch())
            if status:
                print "ERROR:  Cannot pull! %s" % output
        else:
            (status,output) = commands.getstatusoutput("git pull")
            if status:
                print "ERROR:  Cannot pull! %s" % output
                quit()
        print "Success!"
    
    #
    # GitConnect Constructor
    #
    def __init__(self):
        currentDir = os.getcwd()
        currentBranch = self.getBranch()
        #print currentBranch + " in '" + currentDir + "'."
    
    #
    # check if there are any unsaved changes since last commit. if there are,
    # fail and tell the user to use git stash or git commit
    #
    def checkForUnsavedChanges(self):
        output = self.checkForRepository()
        #if "git status" returns an error..."
        if commands.getstatusoutput("git status --porcelain")[1]:
            WARN("WARNING: changes have been made to source code!")
            print "         use git stash or git commit to save changes"
            quit()
        else:
            return
        
    #
    # Checks out existing branch for CASE_NO
    #
    def checkoutExistingBranch(self,CASE_NO):

        output = self.__checkoutExistingBranch(CASE_NO)
        if not output:
            print "ERROR: could not checkout existing branch: %s" % output
            raise Exception("stacktraceplease")
            quit()

        #print bcolors.WARNING + output + bcolors.ENDC

        self.pull()


    
    #
    # Private method: Checks out and existing branch for CASE_NO
    #
    def __checkoutExistingBranch(self, CASE_NO):
        return self.__checkoutExistingBranchRaw("work-%d" % CASE_NO)
        
    def __checkoutExistingBranchRaw(self,arg):
        (checkoutNewBranchStatus, output) = commands.getstatusoutput("git checkout {0}".format(arg))
        if(checkoutNewBranchStatus):
            print output
            return False
        (status,output) = commands.getstatusoutput("git submodule update")
        if status:
            print "Error updating a submodule"
        return True
    #
    # Checks out branch given branch name
    #
    def checkoutExistingBranchRaw(self,BRANCH_NAME):
        result = self.__checkoutExistingBranchRaw(BRANCH_NAME)
        if not result:
            print "ERROR: could not checkout existing branch: %s" % BRANCH_NAME
            quit()
        return result

    #
    # Checkout fromSpec and set up tracking
    #
    def createNewRawBranch(self, branchName, fromSpec):
        #check fromspec
        if(fromSpec):
            if fromSpec=="Undecided":
                print "Undecided isn't a valid fromspec.  (Maybe set the milestone on the ticket?)"
                quit()
            self.checkoutExistingBranchRaw(fromSpec)
        #regardless, we need our integration branch to be up to date
        self.pull()
        
        # create branch for and check it out
        self.checkoutExistingBranchRaw("-b {0}".format(branchName))
                                       
        # push changes
        self.pushChangesToOriginBranch(branch=branchName)

        self.setUpstream(branchName, "remotes/origin/{0}".format(branchName))                               
        return branchName
    
    #
    # Checkout fromSpec and set up tracking
    #
    def createNewWorkBranch(self, CASE_NO, fromSpec):
        return self.createNewRawBranch("work-{0}".format(CASE_NO),fromSpec)
    
    #
    # gets list of branches. if CASE_NO branch exists, check it out. Otherwise
    # create a new branch, check into it, push something up to master, make it track, and return.
    #
    def checkoutBranch(self, CASE_NO, fromSpec,fbConnection):

        
        # get output from git branch command
        (branchStatus, branchOutput) = commands.getstatusoutput("git branch")
        
        #fetch git repo information
        self.fetch()
        
        # check if a branch for CASE_NO exists
        # if it does, check it out
        if self.__checkoutExistingBranch(CASE_NO):
            if fromSpec:
                WARN("Ignoring your fromspec.  To override, re-try with after a git checkout master && git branch -D work-%d && git push origin :work-%d" %(CASE_NO,CASE_NO))
                WARN("THIS DESTRUCTIVE COMMAND DELETES ANY WORK ON work-%d, USE WITH CAUTION!" % CASE_NO)
            self.pull()
            return
            
        # if a branch does not exist, create one and check it out
        else:
            if not fromSpec:
                #try to fill automatically from FB
                fromSpec = fbConnection.getIntegrationBranch(CASE_NO)
            self.createNewWorkBranch(CASE_NO, fromSpec)
            return
                
    #
    # checkout master
    #
    def checkoutMaster(self):
        # try to checkout master
        self.checkoutExistingBranchRaw("master")
    
    #
    # push changes from branch to origin
    #
    def pushChangesToOriginBranch(self, branch="master"):
        # try to push changes
        (checkoutStatus, output) = commands.getstatusoutput("git push origin {0}".format(branch))
        if(checkoutStatus):
            print "ERROR: Could not push to origin!"
            quit()

   #
   # set upstream tracking information
   #
    def setUpstream(self, branch, upstreamPath):
        (status,output) = commands.getstatusoutput("git branch --set-upstream {0} {1}".format(branch, upstreamPath))
        if status:
            print "ERROR: Can't make this a tracking branch..."
            print output
            raise Exception("Can't set upstream")
    
import unittest


class TestSequence(unittest.TestCase):
    def setUp(self):
        self.g = GitConnect()

    def test_pretendmerge(self):
        self.g.mergeIn("master",pretend=True)


if __name__ == '__main__':
    unittest.main(failfast=True)
    
    
    
