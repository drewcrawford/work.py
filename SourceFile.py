import os

class SourceFile:
    validFileExtensions = (".m", ".h")

    errors = None
    classes = None
    name = None
    ext = None
    contents = None
    root = None

    def __init__(self, fileName, rootDir=None):
        self.ext = SourceFile.filterLineEndings(fileName)
        if self.ext:
            path = fileName.split("/")
            self.name = path[len(path)-1][:-len(self.ext)]
            if not rootDir:
                rootDir = os.getcwd()
            self.root = rootDir
            self.errors = list()
            self.classes = list()

    @staticmethod
    def filterLineEndings(fileName):
        for ext in SourceFile.validFileExtensions:
            if fileName.endswith(ext):
                return ext
        return False

    def reportError(self, error, match=None, suppressText=False):
        if match:
            lineno = self.get().count("\n", 0, match.start())+1
            if not suppressText:
                badString = match.group(0)
            else:
                badString = None
        else:
            lineno = -1
            badString = None
        self.errors.append((error, lineno, badString))

    def hasErrors(self):
        return len(self.errors)

    def getErrors(self):
        for errorTuple in self.errors:
            if errorTuple[2]:
                yield "Line %s: %s (%s)" % (errorTuple[1], errorTuple[0], errorTuple[2])
            else:
                yield "Line %s: %s" % (errorTuple[1], errorTuple[0])

    def getRawErrors(self):
        for errorTuple in errors:
            yield errorTuple

    def fileWithExtension(self, extension):
        if os.path.exists("%s%s" % (self.name, extension)):
            return SourceFile("%s%s" % (self.name, extension))
        return None

    def get(self):
        if not self.contents:
            current = os.getcwd()
            os.chdir(self.root)
            with open(self.__str__()) as file:
                self.contents = file.read()
            os.chdir(current)
        return self.contents

    def set(self, contents):
        self.contents = contents

    def save(self):
        current = os.getcwd()
        os.chdir(self.root)
        with open("%s%s" % (self.name, self.ext), "w") as file:
            file.write(self.contents)
        os.chdir(current)

    def replace(self, find, replace):
        self.contents = self.contents.replace(find, replace)

    def type(self):
        if self.ext == ".m":
            return "objc"
        if self.ext == ".h":
            return "header"

    def __str__(self):
        return "%s%s" % (self.name, self.ext)