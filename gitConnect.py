from subprocess import Popen, PIPE
import os
import commands

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
    # Returns the branch, else quits
    #
    def getBranch(self):
        output = self.checkForRepository()
        output = output.split("\n")[0].split(" ")[3]
        return output
    #
    # Performs a git fetch
    #
    def fetch(self):
        self.checkForRepository()
        (status,output) = commands.getstatusoutput("git fetch")
        if status:
            print "ERROR:  Cannot fetch! %s" % output
            quit()
    
    #
    # Performs a git pull
    #
    def pull(self):
        self.checkForRepository()
        (status,output) = commands.getstatusoutput("git pull")
        if status:
            print "ERROR:  Cannot pull! %s" % output
            quit()
    
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
            print "WARNING: changes have been made to source code!"
            print "         use git stash or git commit to save changes"
            quit()
        else:
            return
            
    #
    # gets list of branches. if CASE_NO branch exists, check it out. Otherwise
    # create a new branch, check into it, and return.
    #
    def checkoutBranch(self, CASE_NO, fromSpec):           
        #make sure there is a valid CASE_NO specified
        if(not CASE_NO):
            print "ERROR: CASE_NO not specified. Please specify a working case!"
            quit()
        
        # get output from git branch command
        (branchStatus, branchOutput) = commands.getstatusoutput("git branch")
        
        # if it broke
        if(branchStatus):
            print "ERROR: There's a branch problem in your repository!"
            quit()
            
        else:
            # check if a branch for CASE_NO exists
            # if it does, check it out
            if("work-{0}".format(CASE_NO) in branchOutput):
                (checkoutStatus, output) = commands.getstatusoutput("git checkout work-{0}".format(CASE_NO))
                if(checkoutStatus):
                    print "ERROR: Git could not checkout working branch!"
                    quit()
                else:
                    return "work-{0}".format(CASE_NO)
            # if a branch does not exist, create one and check it out
            else:
                #check fromspec
                if(fromSpec):
                    (fromSpecStatus, output) = commands.getstatusoutput("git checkout {0}".format(fromSpec))
                    if(fromSpecStatus):
                        print "Could not checkout FROMSPEC"
                        quit()
                
                # create branch for new CASE_NO
                (createBranchStatus, output) = commands.getstatusoutput("git branch work-{0}".format(CASE_NO))
                if(createBranchStatus):
                    print "ERROR: could not create new branch from case no: " + str(CASE_NO)
                    quit()
                else:
                    (checkoutNewBranchStatus, output) = commands.getstatusoutput("git checkout work-{0}".format(CASE_NO))
                    if(checkoutNewBranchStatus):
                        print "ERROR: could not checkout newly created branch"
                        quit()
                    else:
                        return "work-{0}".format(CASE_NO)
                
    #
    # checkout master
    #
    def checkoutMaster(self):
        # try to checkout master
        (checkoutStatus, output) = commands.getstatusoutput("git checkout master")
        
        if(checkoutStatus):
            print "ERROR: Could not checkout master. Run git status, and try checking out master again!"
            quit()
    
    #
    # push changes from branch to origin
    #
    def pushChangesToOriginBranch(self, branch="master"):
        # try to push changes
        (checkoutStatus, output) = commands.getstatusoutput("git push origin {0}".format(branch))
        
        if(checkoutStatus):
            print "ERROR: Could not push to origin!"
            quit()
    
    
    
    
    
    
    
