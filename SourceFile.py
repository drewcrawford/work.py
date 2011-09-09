import os

class SourceFile (object):
    validFileExtensions = (".m", ".h")

    errors = list()
    classes = list()
    name = None
    ext = None
    contents = None
    root = None

    def __init__(self, fileName, rootDir=None):
        self.ext = SourceFile.filterLineEndings(fileName)
        self.name = fileName[:-len(self.ext)]
        if not rootDir:
            rootDir = os.getcwd()
        self.root = rootDir

    def __new__(cls, *args, **kwargs):
        fileName = args[0]
        ext = SourceFile.filterLineEndings(fileName)
        if ext == False:
            #print "Skipping unknown file type %s" % fileName
            return None
        return object.__new__(cls)

    @staticmethod
    def filterLineEndings(fileName):
        for ext in SourceFile.validFileExtensions:
            if fileName.endswith(ext):
                return ext
        return False

    def reportError(self, error, match=None):
        if match:
            lineno = self.get().count("\n", 0, match.start())+1
            badString = match.group(0)
        else:
            lineno = -1
            badString = None
        self.errors.append((error, lineno, badString))

    def hasErrors(self):
        return len(self.errors)

    def getErrors(self):
        for errorTuple in errors:
            yield "Line %s: %s (%s)" % (errorTuple[1], errorTuple[0], errorTuple[2])

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

    def __str__(self):
        return "%s%s" % (self.name, self.ext)

    #note that this will be called even if __init__ failed (IE. this is the opposite of __new__, not __init__)
    def __del__(self):
        pass