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
                if fileName.endswith(".h") and os.path.exists("%s.m" % fileName[:-2]):
                    out = self.fixObjCPropertiesInHeader(out)
                    with open("%s.m" % fileName[:-2]) as implementation:
                        mout = self.fixObjCPropertiesInImplementation(implementation.read())
                    if not self.pretend:
                        with open("%s.m" % fileName[:-2], 'w') as implementation:
                            implementation.write(mout)
                if self.pretend and out is False:
                    return False
            if not self.pretend:
                with open(fileName, 'w') as file:
                    file.write(out)
        os.chdir(self.originalDir)
        return True

#fixing Objective C properties
    def fixObjCPropertiesInHeader(self, file):
        objCProperty.properties = list()
        file = objCProperty.propertiesInFile(file, self.pretend)
        if self.pretend and not file:
            return False
        return file

    def fixObjCPropertiesInImplementation(self, file):
        file = objCProperty.propertiesInFile(file, self.pretend)
        if self.pretend and not file:
            return False
        file = objCProperty.fixSynthesis(file, self.pretend)
        if self.pretend and not file:
            return False
        file = objCProperty.fixMemoryInImplementation(file, self.pretend)
        if self.pretend and not file:
            return False
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
    properties = list()

    findIVarExp = r'(?:(?:__block|IBOutlet)\s+)*%s\s+%s\s*;'
    atomicity = "atomic"
    memory = "retain"
    block = ""
    iboutlet = ""
    type = None
    name = None
    valid = True
    property = False

    def __init__(self, match, property):
        self.property = property
        if self.property:
            self.makeProperty(match)
        else:
            self.makeIVar(match)

    def makeProperty(self, match):
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

    def makeIVar(self, match):
        self.atomicity = match[0];
        if match[1]:
            if match[1].strip().lower() == "__block":
                self.block = match[1]
            elif match[1].strip() == "IBOutlet":
                self.iboutlet = match[1]
        if match[2]:
            if match[2].strip().lower() == "__block":
                self.block = match[2]
            elif match[2].strip() == "IBOutlet":
                self.iboutlet = match[2]
        self.type = match[3]
        self.name = match[4]

    @staticmethod
    def propertiesInFile(file, pretend):
        findProperty = re.compile(r'@property\s+(?:\(((?:[^\,)],?)+)\)\s+)?((?:__block|IBOutlet)\s+)?((?:__block|IBOutlet)\s+)?(\S+)\s+(\S+?)\s*;', re.IGNORECASE)
        matches = findProperty.finditer(file)
        properties = list()
        valid = True
        for match in matches:
            #print match.groups()
            property = objCProperty(match, True)
            valid = valid and property.valid
            if pretend and not valid:
                return False
            file = file.replace(match.group(0), property.__str__())
            objCProperty.properties.append(property)
        (file, valid) = objCProperty.findIVars(file, pretend)
        if pretend and not valid:
            return False
        #print "------------"
        #for item in objCProperty.properties:
        #    print item
        return file

    @staticmethod
    def findIVars(file, pretend):
        findIVarSection = re.compile(r'@interface.*?\{([^}]*?)\}', re.DOTALL)
        findIVars = re.compile(r'(\s*)((?:__block|IBOutlet)\s+)?((?:__block|IBOutlet)\s+)?([^\s;]+)\s+((?:[^\s;]+\s*,?\s*)+);', re.DOTALL)
        section = findIVarSection.search(file)
        matches = findIVars.finditer(section.group(1))
        out = list()
        valid = True
        for match in matches:
            names = match.group(5).split(",")
            if len(names) > 1:
                valid = False
            type = match.group(4)
            if type.endswith("*"):
                names[0] = "*%s" % names[0].strip()
                type = type[:-1]
                valid = False
            if pretend and not valid:
                return False
            ivars = list()
            for name in filter(lambda x:x not in map(lambda x:x.name, objCProperty.properties), names):
                ivar = objCProperty((match.group(1), match.group(2), match.group(3), type.strip(), name.strip()), False)
                ivars.append(ivar.__str__())
                objCProperty.properties.append(ivar)
            file = file.replace(match.group(0), "".join(ivars))
        return (file, valid)

    @staticmethod
    def fixSynthesis(file, pretend):
        findSynthesis = re.compile(r'(\s*)@synthesize\s*((?:[^\s;]+\s*,?\s*)+);', re.DOTALL | re.IGNORECASE)
        matches = findSynthesis.finditer(file)
        for match in matches:
            names = match.group(2).strip().split(",")
            if len(names) > 1 and pretend:
                return False
            out = list()
            for name in names:
                out.append("%s@synthesize %s;" % (match.group(1), name.strip()))
            file = file.replace(match.group(0), "".join(out))
        return file

    @staticmethod
    def fixMemoryInImplementation(file, pretend):
        findMethod = r'%s\s*\(\s*%s\s*\)\s*%s[^\{]*\{(.*?)\n\}'
        #findInit = re.compile(r'-\s*\(\s*void\s*\)\s*init[^\{]*\{(.*?)\n\}', re.IGNORECASE | re.DOTALL)
        #findDealloc = re.compile(r'-\s*\(\s*void\s*\)\s*dealloc\s*\{(.*?)\n\}', re.IGNORECASE | re.DOTALL)
        #findViewDidLoad = re.compile(r'-\s*\(\s*void\s*\)\s*viewDidLoad\s*\{(.*?)\n\}', re.IGNORECASE | re.DOTALL)
        #findViewDidUnload = re.compile(r'-\s*\(\s*void\s*\)\s*viewDidUnload\s*\{(.*?)\n\})', re.IGNORECASE | re.DOTALL)
        findPropertyAssignment = r'[^\.\w]%s\s*='
        findValidPropertyAssignment = r'self\.%s\s*=\s*'
        findCustomSetter = findMethod % (r'-', r'void', r'set%s:')

        #fix property assignment without self.
        for property in objCProperty.properties:
            if property.property and property.memory != "readonly":
                name = property.name
                if property.name.startswith("*"):
                    name = name[1:]
                exp = re.compile(findPropertyAssignment % name)
                matches = exp.finditer(file)
                #if pretend, count how many we would fix and then subtract the number we revert in custom setters. If that's > 0, pretend fail
                count = 0
                for match in matches:
                    count += 1
                    if not pretend:
                        file = file.replace(match.group(0), "%sself.%s" % (match.group(0)[0], match.group(0)[1:]))
                ucfirstname = "%s%s" % (name[0].upper(), name[1:])
                exp = re.compile(findCustomSetter % ucfirstname, re.DOTALL)
                setter = exp.search(file)
                if setter:
                    exp = re.compile(findValidPropertyAssignment % name)
                    matches = exp.finditer(setter.group(1))
                    for match in matches:
                        count -= 1
                        if not pretend:
                            file = file.replace(match.group(0), "%s = " % name)
                if pretend and count != 0:
                    return False
            elif property.property and property.memory == "readonly":
                name = property.name
                if property.name.startswith("*"):
                    name = name[1:]
                exp = re.compile(findValidPropertyAssignment % name)
                matches = exp.finditer(file)
                for match in matches:
                    if pretend:
                        return False
                    file = file.replace(match.group(0), "%s = " % name)
        return file

    def __str__(self):
        if self.property:
            return "@property (%s, %s) %s%s%s %s;" % (self.atomicity, self.memory, self.block, self.iboutlet, self.type, self.name)
        else:
            #atomicty is hacked for ivars to contain the leading whitespace
            return "%s%s%s%s %s;" % (self.atomicity, self.block, self.iboutlet, self.type, self.name)