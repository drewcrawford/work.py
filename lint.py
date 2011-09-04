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

        self.findInit = re.compile(r'-\s*\(\s*void\s*\)\s*init[^\{]*\{(.*?)\}\s*(?:$|-|\+|#|/)', re.IGNORECASE | re.DOTALL)
        self.findDealloc = re.compile(r'-\s*\(\s*void\s*\)\s*dealloc\s*\{(.*?)\}\s*(?:$|-|\+|#|/)', re.IGNORECASE | re.DOTALL)
        self.findViewDidLoad = re.compile(r'-\s*\(\s*void\s*\)\s*viewDidLoad\s*\{(.*?)\}\s*(?:$|-|\+|#|/)', re.IGNORECASE | re.DOTALL)
        self.findViewDidUnload = re.compile(r'-\s*\(\s*void\s*\)\s*viewDidUnload\s*\{(.*?)\}\s*(?:$|-|\+|#|/)', re.IGNORECASE | re.DOTALL)

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

    def filterLineEndings(self, fileName):
        for ext in self.validFileExtensions:
            if fileName.endswith(ext):
                return True
        return False

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
                if fileName.endswith(".h"):
                    out = self.fixObjCPropertiesInHeader(out)
                if self.pretend and out is False:
                    return False
            if not self.pretend:
                with open(fileName, 'w') as file:
                    file.write(out)
        os.chdir(self.originalDir)
        return True

#fixing Objective C properties
    def fixObjCPropertiesInHeader(self, file):
        file = objCProperty.propertiesInFile(file, self.pretend)
        return file

    def getPropertySet(self, file, propertyName):
        exp = re.compile(r'self.%s\s*=\s*(.*?)\s*;' % propertyName, re.IGNORECASE)

    def getDealloc(self, file):
        pass

#fixing braces and whitespace
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

class objCProperty:
    findIVarExp = r'(?:(?:__block|IBOutlet)\s+)*%s\s+%s\s*;'
    atomicity = "atomic"
    memory = "retain"
    block = ""
    iboutlet = ""
    type = None
    name = None
    valid = True

    def __init__(self, match):
        #read in the property modifiers
        if match.group(1):
            for modifier in match.group(1).lower().split(","):
                modifier = modifier.strip()
                if modifier.endswith("atomic"):
                    self.atomicity = modifier
                elif modifier in ("assign", "copy", "readonly", "retain"):
                    self.memory = modifier
                else:
                    print "Unsupported property modifier %s" % modifier
        if match.group(3): #IBOutlets
            if self.atomicity is not "nonatomic" or self.memory is not "retain" or self.block is not "":
                self.valid = False
                self.atomicity = "nonatomic"
                self.memory = "retain"
                self.block = "";
            self.iboutlet = match.group(2)
        #save whether or not this is declared __block
        if self.iboutlet is "" and match.group(2):
            self.block = match.group(2)

        self.type = match.group(4).strip()
        self.name = match.group(5).strip()
        if self.type.endswith("*"):
            self.valid = False
            self.name = "*%s" % self.name
            self.type = self.type[:-1];
        #make sure objects are declared copy when they could be mutable but aren't the mutable version
        if self.type in ("NSArray", "NSSet", "NSDictionary", "NSString"):
            if self.memory is not "copy":
                self.valid = False
                self.memory = "copy"
        #make sure all pointers are declared retain, unless explictly postfixed with "Copy" or "Assign
        elif self.memory not in ("retain", "readonly") and self.name.startswith("*") and not (self.name.endswith("Copy") or self.name.endswith("Assign")):
            self.memory = "retain"
            self.valid = False

    @staticmethod
    def propertiesInFile(file, pretend):
        findProperty = re.compile(r'@property\s+(?:\(((?:[^\,)],?)+)\)\s+)?((?:__block|IBOutlet)\s+)?((?:__block|IBOutlet)\s+)?(\S+)\s+(\S+)', re.IGNORECASE)
        matches = findProperty.finditer(file)
        properties = list()
        (file, valid) = objCProperty.findIVars(file)
        for match in matches:
            #print match.groups()
            property = objCProperty(match)
            valid = valid and property.valid
            if pretend and not valid:
                return False
            file = file.replace(match.group(0), property.__str__())
        return file

    @staticmethod
    def findIVars(file):
        findIVarSection = re.compile(r'@interface.*?\{([^}]*?)\}', re.DOTALL)
        findIVars = re.compile(r'(\s*(?:(?:__block|IBOutlet)\s+)*)([^\s;]+)\s+((?:[^\s;]+\s*,?\s*)+);', re.DOTALL)
        section = findIVarSection.search(file)
        matches = findIVars.finditer(section.group(1))
        out = list()
        valid = True
        for match in matches:
            names = match.group(3).split(",")
            if len(names) > 1:
                valid = False
            type = match.group(2)
            if type.endswith("*"):
                names[0] = "*%s" % names[0].strip()
                type = type[:-1]
                valid = False
            out = list()
            for name in names:
                out.append("%s%s %s;" % (match.group(1), type, name.strip()))
            file = file.replace(match.group(0), "".join(out))
        return (file, valid)

    def __str__(self):
        return "@property (%s, %s) %s%s%s %s" % (self.atomicity, self.memory, self.block, self.iboutlet, self.type, self.name)