from JucheLog.juchelog import juche
import os
import sys
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[43m\033[1;34m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


class GitConnect:


    @staticmethod
    def clone(url,into):
        import subprocess
        import shlex
        args = shlex.split("git clone %s %s" % (url,into))
        pipe = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False,universal_newlines=True)
        (output,err) = pipe.communicate()
        if pipe.returncode != 0:
            raise Exception("Can't clone repository %s" % output+err)
        g = GitConnect(into)
        g.submoduleUpdate()
        return g


    #
    # repo-config
    #
    def repoConfig(self,key,value):
        self.statusOutputExcept("git config %s %s" % (key,value))

    def submoduleUpdate(self):
        import shlex
        import subprocess
        args = shlex.split("git submodule init")
        pipe = subprocess.Popen(args,stdout=subprocess.PIPE,cwd=self.wd,stderr=subprocess.PIPE,shell=False,universal_newlines=True)
        (output,err) = pipe.communicate()
        if pipe.returncode:
            raise Exception("Error initing a submodule" + output + err)
        args = shlex.split("git submodule update")
        pipe = subprocess.Popen(args,stdout=subprocess.PIPE,cwd=self.wd,stderr=subprocess.PIPE,shell=False,universal_newlines=True)
        (output,err) = pipe.communicate()
        if pipe.returncode:
            raise Exception("Error initing a submodule" + output + err)

    #
    # Add files to the index
    #
    def add(self,path_desc):
        self.statusOutputExcept("git add %s" % path_desc)

    def commit(self,msg):
        self.statusOutputExcept("git commit -m '%s'" % msg)

    def commitAll(self, msg):
        self.statusOutputExcept("git commit -a -m '%s'" % msg)

    #
    # status_output_wrapper
    #
    def statusOutput(self,cmd,wd=None):
        if not wd: wd = self.wd
        import subprocess
        import shlex
        args = shlex.split(cmd)
        #with help from http://stackoverflow.com/questions/1193583/what-is-the-multiplatform-alternative-to-subprocess-getstatusoutput-older-comman
        pipe = subprocess.Popen(args,cwd=wd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False,universal_newlines=True)
        (output,stderr) = pipe.communicate()
        output += stderr
        sts = pipe.returncode
        #print "sts is",sts
        if sts is None: sts = 0
        return sts,output

    def statusOutputExcept(self,cmd):
        (status,output) = self.statusOutput(cmd)
        if status:
            raise Exception("Command returned invalid status: %d; %s; %s" % (status,cmd,output))

    def resetHard_INCREDIBLY_DESTRUCTIVE_COMMAND(self):
        import os
        for root,dirs,files in os.walk(self.wd):

            self.statusOutput("git clean -d -x -ff",wd=root)
            self.statusOutput("git reset --hard",wd=root)
            self.statusOutput("git submodule update",wd=root)

    #
    # Checks to see if we're in a Git Repo
    #
    def checkForRepository(self):
        (status, output) = self.statusOutput("git status")
        if(status):
            juche.error("Not in git repository! Check your current directory!")
            raise Exception("stacktraceplease")
        else:
            return output


    #
    # Return (user,repo) for current working copy
    #
    def getUserRepo(self):
        (status,output) = self.statusOutput("git remote show origin")
        import re
        userRepo = re.search("(?<=Fetch URL:)[^:]+:(.*)",output).group(1).split("/")
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
    # Gets the current commit ID (SHA)
    #
    def getSHA(self):
        (status,output) = self.statusOutput("git rev-parse HEAD")
        return output.strip()

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
        (status,output) = self.statusOutput("git fetch")
        if status:
            juche.error("ERROR:  Cannot fetch! %s" % output)
            raise Exception("stacktraceplease")

    def __mergeInPretend(self,BRANCH_NAME): #http://stackoverflow.com/questions/501407/is-there-a-git-merge-dry-run-option/6283843#6283843
        self.checkForUnsavedChanges()
        (status,output) = self.statusOutput("git merge --no-commit --no-ff %s" % BRANCH_NAME)
        if status:
            juche.dictate(output=output)
            juche.warning("gitConnect __mergeInPretend: merge %s will not apply cleanly.  " % BRANCH_NAME)
        self.resetHard_INCREDIBLY_DESTRUCTIVE_COMMAND()
        #if you see an exception on the line below, we failed to roll back the merge
        self.checkForUnsavedChanges()
        return status==0

    #
    #
    #
    def mergeIn(self,BRANCH_NAME,pretend=False):
        if pretend:
            return self.__mergeInPretend(BRANCH_NAME)
        juche.dictate(merging_in=BRANCH_NAME)
        (status,output) = self.statusOutput("git merge --no-ff %s" % BRANCH_NAME)
        juche.info(output)
        if status:
            juche.error("merge was unsuccessful.")
            # play sounds!
            self.statusOutput ("afplay -v 7 %s/media/ohno.aiff" % sys.prefix)
            raise Exception("stacktraceplease")
        else:
            # play sounds!
            from work import get_setting_dict
            if get_setting_dict().has_key("disablesounds") and get_setting_dict()["disablesounds"]=="YES":
                pass
            else:
                self.statusOutput ("afplay -v 7 %s/media/hooray.aiff" % sys.prefix)
        juche.info("Use 'git push' to ship.")

    def needsPull(self):
        (status,output) = self.statusOutput("git status")
        if status: return True
        if output.find("Your branch is behind") != -1:
            return True
        return False


    #
    # Performs a git pull
    #
    def pull(self):
        self.checkForRepository()
        import ConfigParser
        c = ConfigParser.ConfigParser()
        if self.wd:
            path = self.wd + "/.git/config"
        else:
            path =".git/config"
        import os
        for i in range(0,30):
            if os.path.exists(path): break
            path = "../" + path
            if i==30:
                raise Exception("Not a git repository?")

        file = open(path)
        str = file.read()
        file.close()

        juche.dictate(pull=1)
        if self.getBranch() not in str:
            juche.warn( "%s is not a tracking branch. Attempting to fix..." % self.getBranch())
            try:
                self.setUpstream(self.getBranch(),"remotes/origin/{0}".format(self.getBranch()))
                juche.info("Success!")
            except:
                juche.error("DID NOT AUTOMATICALLY FIX BRANCH UPSTREAM / TRACKING.  PLEASE FILE A BUG.")

            (status,output) = self.statusOutput("git pull origin %s" % self.getBranch())
            if status:
                juche.error("Cannot pull! %s" % output)
        else:
            (status,output) = self.statusOutput("git pull")
            if status:
                juche.error("ERROR:  Cannot pull! %s" % output)
                raise Exception("stacktraceplease")
        self.submoduleUpdate()
        juche.info("Success!")

    #
    # GitConnect Constructor
    #
    def __init__(self,wd=None):
        if wd:
            if not os.path.exists(wd):
                raise IOError("Directory not found.")
        self.wd=wd

    #
    # check if there are any unsaved changes since last commit. if there are,
    # fail and tell the user to use git stash or git commit
    #
    def checkForUnsavedChanges(self):
        output = self.checkForRepository()
        #if "git status" returns an error..."
        if self.statusOutput("git status --porcelain")[1]:
            juche.warn("changes have been made to source code!")
            juche.warn("         use git stash or git commit to save changes")
            raise Exception("stacktraceplease")
        else:
            return

    #
    # Checks out existing branch for CASE_NO
    #
    def checkoutExistingBranch(self,CASE_NO):

        output = self.__checkoutExistingBranch(CASE_NO)
        if not output:
            juche.error("could not checkout existing branch: %s" % output)
            raise Exception("stacktraceplease")

        #print bcolors.WARNING + output + bcolors.ENDC

        self.pull()
        return True



    #
    # Private method: Checks out and existing branch for CASE_NO
    #
    def __checkoutExistingBranch(self, CASE_NO):
        return self.__checkoutExistingBranchRaw("work-%d" % CASE_NO)

    def __checkoutExistingBranchRaw(self,arg):
        juche.dictate(double_checkout_existing_branch_raw=arg)
        (checkoutNewBranchStatus, output) = self.statusOutput("git checkout {0}".format(arg))
        if(checkoutNewBranchStatus):
            juche.info(output)
            return False
        (status,output) = self.statusOutput("git submodule init")
        if status:
            juche.error("could not init submodule: %s",output)
        (status,output) = self.statusOutput("git submodule update")
        if status:
            juche.error("Error updating a submodule %s",output)
        return True
    #
    # Checks out branch given branch name
    #
    def checkoutExistingBranchRaw(self,BRANCH_NAME):
        result = self.__checkoutExistingBranchRaw(BRANCH_NAME)
        if not result:
            juche.error("ERROR: could not checkout existing branch: %s" % BRANCH_NAME)
            raise Exception("stacktraceplease")
        return result

    #
    # Checkout fromSpec and set up tracking
    #
    def createNewRawBranch(self, branchName, fromSpec):
        #check fromspec
        if(fromSpec):
            if fromSpec=="Undecided":
                juche.error("Undecided isn't a valid fromspec.  (Maybe set the milestone on the ticket?)")
                raise Exception("stacktraceplease")
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
        (branchStatus, branchOutput) = self.statusOutput("git branch")

        #fetch git repo information
        self.fetch()

        # check if a branch for CASE_NO exists
        # if it does, check it out
        if self.__checkoutExistingBranch(CASE_NO):
            if fromSpec:
                juche.warn("Ignoring your fromspec.  To override, re-try with after a git checkout master && git branch -D work-%d && git push origin :work-%d" %(CASE_NO,CASE_NO))
                juche.warn("THIS DESTRUCTIVE COMMAND DELETES ANY WORK ON work-%d, USE WITH CAUTION!" % CASE_NO)
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
        (checkoutStatus, output) = self.statusOutput("git push origin {0}".format(branch))
        if(checkoutStatus):
            juche.error("ERROR: Could not push to origin!")
            raise Exception("stacktraceplease")

   #
   # set upstream tracking information
   #
    def setUpstream(self, branch, upstreamPath):
        (status,output) = self.statusOutput("git branch --set-upstream {0} {1}".format(branch, upstreamPath))
        if status:
            juche.error("ERROR: Can't make this a tracking branch...")
            juche.error(output)
            raise Exception("Can't set upstream")

import unittest


class TestSequence(unittest.TestCase):
    def setUp(self):
        self.g = GitConnect()


    def test_merge_pretend(self):
        from os import system
        system("rm -rf /tmp/g")
        GitConnect.clone("git://github.com/drewcrawford/work.py.git","/tmp/g")
        g = GitConnect("/tmp/g")
        self.assertTrue(g.mergeIn("remotes/origin/merge_a",pretend=True))
        self.assertTrue(g.mergeIn("remotes/origin/merge_b",pretend=True))
        g.mergeIn("remotes/origin/merge_a") #no pretend
        self.assertFalse(g.mergeIn("remotes/origin/merge_b",pretend=True))

        system("rm -rf /tmp/g")


if __name__ == '__main__':
    unittest.main(failfast=True)
