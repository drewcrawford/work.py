from __future__ import with_statement
import re
import sys
import getopt
import commands
import os

class Lint:
    toOneTrueBraceStyle = None
    toOneTrueBraceStyle_elsePatch = None
    fromOneTrueBraceStyle = None
    fromOneTrueBraceStyle_elsePatch = None
    fixBraceIndentation = None
    validFileExtensions = (".m", ".h")
    pretend = False
    sameLine = False
    files = None
    originalDir = None

    def __init__(self, flags):
        self.toOneTrueBraceStyle = re.compile(r'\s+\{', re.DOTALL)
        self.toOneTrueBraceStyle_elsePatch = re.compile(r'\}\s*else\s*\{', re.DOTALL)
        self.fromOneTrueBraceStyle = re.compile(r'\s*\{( |\t)*')
        self.fromOneTrueBraceStyle_elsePatch = re.compile(r'(\s*)\}\s*else')
        self.fixBraceIndentation = re.compile(r'^(( |\t)*)(.*)\n\{', re.MULTILINE)

        self.sameLine = "-s" in flags
        self.pretend = "-p" in flags

        self.originalDir = os.getcwd()
        if "-d" in flags:
            rootDir = flags[flags.index("-d")+1]
        else:
            match = re.search(r':\s+(.+?):\s+', commands.getoutput("$(git rev-parse --show-toplevel)"))
            rootDir = match.group(1)
        os.chdir(rootDir)
        print "Processing files in %s" % os.getcwd()

        if "--all" in flags:
            os.chdir(self.originalDir)
            self.files = filter(self.filterLineEndings, commands.getoutput("find %s" % rootDir).strip().split("\n"))
        else:
            status = commands.getoutput("git status")
            match = re.search(r'branch\s+(.+?)\s*$', status, re.IGNORECASE | re.MULTILINE)
            changedFiles = commands.getoutput("git diff --name-only remotes/origin/%s ." % match.group(1))
            print changedFiles
            self.files = filter(self.filterLineEndings, changedFiles.strip().split("\n"))

    @staticmethod
    def run():
        try:
            opts, args = getopt.getopt(sys.argv, "snd:", ["all"])
            linter = Lint(args[1:])
            ret = linter.process()
            if ret is False:
                print "Lint analyses failed!"
        except getopt.GetoptError:
            Lint.usage()

    #Returns true everything analyzed cleanly
    @staticmethod
    def analyze():
        linter = Lint(["lint", "-n", "-u", "-p"])
        ret = linter.process()
        if ret is False:
            print "Lint analyses failed!"
        return ret

    @staticmethod
    def usage():
        print "Usage: work.py lint (-s | -n) [-au] [-d DIR]"
        print "-p     Analyze for compliance, don't actually write anything"
        print "-s     Converts to braces on the same line"
        print "-n     Converts to braces on a new line\n\t(default)"
        print "-d     Directory to operate on\n\t(defaults to current directory)"
        print "--all  Process all files in the directory\n\t(overrides -u)"
        print "-u     Process only files that have changed since the last git push\n\t(default)"

    #Returns true if everything analyzed cleanly or if everything was updated to analyze cleanly
    def process(self):
        for fileName in self.files:
            with open(fileName) as file:
                out = self.convertLineEndings(file.read())
                if self.pretend and out is False:
                    return False
            if not self.pretend:
                with open(fileName, 'w') as file:
                    file.write(out)
        os.chdir(self.originalDir)
        return True

    def filterLineEndings(self, fileName):
        for ext in self.validFileExtensions:
            if fileName.endswith(ext):
                return True
        return False

    def convertToOneTrueBraceStyle(self, input):
        ret = self.toOneTrueBraceStyle.replace(" {", input)
        #patch else blocks together
        return self.toOneTrueBraceStyle_elsePatch("} else {", ret);

    def convertFromOneTrueBraceStyle(self, input):
        ret = self.fromOneTrueBraceStyle.sub("\n{", input);
        #patch else blocks together
        return self.fromOneTrueBraceStyle_elsePatch.sub(r'\1}\1else', ret);

    def fixBraceIndent(self, input):
        return self.fixBraceIndentation.sub(r'\1\3\n\1{', input)

    def convertLineEndings(self, file):
        if self.sameLine:
            function = self.convertToOneTrueBraceStyle
        else:
            function = self.convertFromOneTrueBraceStyle

        findQuotedString = re.compile(r'"(?:[^"\\]*?(?:\\.[^"\\]*?)*?)"', re.DOTALL)
        notStrings = findQuotedString.split(file)
        strings = findQuotedString.finditer(file)

        for i in range(0, len(notStrings)):
            temp = function(notStrings[i])
            if self.pretend and notStrings[i] != temp:
                return False
            notStrings[i] = temp

        ret = notStrings[0]
        for i in range(0, len(notStrings)-1):
            ret += strings.next().group(0) + notStrings[i+1]
        if not self.sameLine:
            ret = self.fixBraceIndent(ret)
        return ret;