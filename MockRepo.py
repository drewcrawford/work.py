if __name__=="__main__":
    __builtins__.LOGGLY_KEY="51d07ecb-91d2-4908-8da6-c20b47111d9c"

from gitConnect import GitConnect
from fogbugzConnect import FogBugzConnect
import os
import tempfile

class MockRepo:
    git = None
    dir = None
    fb = None

    def __init__(self, dir=None):
        if not dir:
            dir = "%s/mockrepo/" % tempfile.gettempdir()
            if not os.path.exists(dir):
                os.makedirs(dir)
        self.dir = dir
        self.git = GitConnect(self.dir)
        self.fb = FogBugzConnect()

    def createFile(self, name, contents):
        self.editFile(name, contents)

    def editFile(self, name, contents):
        with open(self.dir+name, "w") as file:
            file.write(contents)

    def readFile(self, name):
        with open(self.dir+name, "r") as file:
            return file.read()

    def gitInit(self):
        self.git.statusOutput("git init", self.dir)

    def gitAdd(self, file):
        self.git.add(file)

    def gitCommit(self, message):
        self.git.commitAll(message)

    def gitPush(self, forceful=False):
        if forceful:
            self.git.statusOutput("git push -u -f")
        else:
            self.git.statusOutput("git push -u")

    def gitPull(self):
        self.git.fetch()
        self.git.pull()
        self.git.submoduleUpdate() #Drew would like to document that this is redundant. Bion would like to document that this redundancy is not clear.

    def gitMerge(self, branch):
        self.git.mergeIn(branch)

    def gitCheckout(self, branch):
        self.git.checkoutExistingBranchRaw(branch)

    #is this name really necessary?
    def wipeRepo__INCREDIBLY__DESTRUCTIVE_COMMAND(self):
        self.git.statusOutputExcept("git push -f --all --delete")
        self.git.statusOutput("rm -Rf .git")
        self.git.statusOutputExcept("git init")
        self.git = GetConnect(self.dir)
        self.git.statusOutputExcept("git remote add origin git@github.com:drewcrawford/SampleProject.git")
        self.createFile("README.txt", "test")
        self.gitAdd("README.txt")
        self.gitCommit("First Commit")
        self.gitPush()

    def ticketReactivate(self, ticket):
        if "Closed" in self.fb.getStatuses(ticket):
            self.fb.reactivate(ticket, 7, "Just testing...")

    def ticketResolve(self, ticket):
        self.fb.resolveCase(ticket)

    def ticketClose(self, ticket):
        self.fb.closeCase(ticket)

    def ticketAssign(self, ticket, ixUser):
        self.fb.assignCase(ticket, ixUser)

    def ticketCreate(self, title):
        return self.fb.createCase(title, 1, 1, 7)

    def ticketSetEstimate(self, ticket, estimate):
        self.fb.setEstimate(ticket, estimate)

#Unit Tests
import unittest
import shutil

class TestSequence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        repo = MockRepo()
        cls.dir = repo.dir
        repo.gitInit()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir)

    def setUp(self):
        self.repo = MockRepo(TestSequence.dir)

    def test_createFile(self):
        self.repo.createFile("test.txt", "This was a triumph!")
        self.assertTrue(os.path.exists(self.repo.dir) and self.repo.readFile("test.txt") == "This was a triumph!")

    def test_editFile(self):
        self.repo.editFile("test.txt", "I'm making a note here: HUGE SUCCESS")
        self.assertTrue(os.path.exists(self.repo.dir) and self.repo.readFile("test.txt") == "I'm making a note here: HUGE SUCCESS")

if __name__ == '__main__':
    unittest.main(failfast=True)
