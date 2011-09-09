class objCProperty:
    properties = list()

    findIVarExp = r'(?:(?:__block|IBOutlet)\s+)*%s\s+%s\s*;'
    atomicity = "atomic"
    memory = "__strong"
    readonly = False
    block = ""
    iboutlet = ""
    type = None
    name = None
    pointer = False
    valid = True
    property = False
    dealloced = False

    def __init__(self, match, property):
        self.property = property
        if self.property:
            self.makeProperty(match)
        else:
            self.makeIVar(match)

    def correctNameAndType(self):
        if self.type.endswith("*"):
            self.valid = False
            self.pointer = "*"
            self.type = self.type[:-1];
        if self.name.startswith("*"):
            self.pointer = "*"
            self.name = self.name[1:]

    def makeProperty(self, match):
        #read in the property modifiers
        if match.group(1):
            for modifier in match.group(1).lower().split(","):
                modifier = modifier.strip()
                if modifier.endswith("atomic"):
                    self.atomicity = modifier
                elif modifier == "readonly":
                    self.readonly = True
                elif modifier in ("strong", "weak", "autoreleasing", "unsafe_unretained", "copy"):
                    self.memory = modifier
                else:
                    print "Unsupported property modifier %s" % modifier
                    self.memory = "UNDEFINED"
                    self.atomicity = "UNDEFINED"
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
        self.correctNameAndType()
        #make sure objects are declared copy when they could be mutable but aren't the mutable version
        if self.type in ("NSArray", "NSSet", "NSDictionary", "NSString"):
            if self.memory is not "copy":
                self.valid = False
                self.memory = "copy"
        #make sure all pointers are declared strong, unless explictly postfixed with "Unsafe" or "Weak"
        elif self.memory not in ("__strong", "readonly") and self.pointer and not (self.name.endswith("Unsafe") or self.name.endswith("Weak")):
            self.memory = "strong"
            self.valid = False

    def makeIVar(self, match):
        self.atomicity = match[0];
        modifiers = (match[1], match[2], match[3])
        for modifier in filter(lambda x:x, modifiers):
            text = modifier.strip().lower()
            if text == "__block":
                self.block = modifier
            elif text == "iboutlet":
                self.iboutlet = modifier
            elif text in ("__strong", "__weak", "__autoreleasing", "__unsafe_unretained"):
                self.memory = modifier
            else:
                print "Unsupported ivar modifier %s" % modifier
                self.memory = "UNDEFINED"
                self.atomicity = "UNDEFINED"
        self.type = match[3]
        self.name = match[4]
        self.correctNameAndType()

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
        findIVars = re.compile(r'(\s*)((?:(__)?\w+)\s+)?((?:(__)?\w+)\s+)?((?:(__)?\w+)\s+)?([^\s;]+)\s+((?:[^\s;]+\s*,?\s*)+);', re.DOTALL)
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
                    setterBlock = setter.group(0)
                    for match in matches:
                        count -= 1
                        if not pretend:
                            setterBlock = setterBlock.replace(match.group(0), "%s = " % name)
                    if not pretend:
                        file = file.replace(setter.group(0), setterBlock)
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

        #fix init/dealloc and viewDidLoad/Unload
        findInit = re.compile(findMethod % (r'-', r'id', r'init'), re.IGNORECASE | re.DOTALL)
        findDealloc = re.compile(findMethod % (r'-', r'void', r'dealloc'), re.IGNORECASE | re.DOTALL)
        findViewDidLoad = re.compile(findMethod % (r'-', r'void', r'viewDidLoad'), re.IGNORECASE | re.DOTALL)
        findViewDidUnload = re.compile(findMethod % (r'-', r'void', r'viewDidUnload'), re.IGNORECASE | re.DOTALL)
        findAssignment = re.compile(r'(\w+)\s*=')

        matches = findInit.finditer(file)
        assignedInInit = list()
        for match in matches:
            matches2 = findAssignment.finditer(match.group(1))
            for match in matches2:
                name = match.group(1)
                if name != "self":
                    assignedInInit.append(name)
        assignedInViewDidLoad = list()
        viewDidLoad = findViewDidLoad.search(file)
        if viewDidLoad:
            matches = findAssignment.finditer(viewDidLoad.group(1))
            for match in matches:
                name = match.group(1)
                if name not in assignedInInit:
                    assignedInViewDidLoad.append(name)
            print assignedInInit
            print assignedInViewDidLoad

            if len(assignedInViewDidLoad) > 0:
                viewDidUnload = findViewDidUnload.search(file)
                if not viewDidUnload:
                    if pretend:
                        return False
                    viewDidUnload = "-(void)viewDidUnload {\n}"
                    file = file.replace(viewDidLoad.group(0), "%s\n\n%s" % (viewDidLoad.group(0), viewDidUnload))
                for property in objCProperty.properties:
                    if property.iboutlet or property.name in assignedInViewDidLoad:
                        #convert [self set%s:nil] calls to self.%s = nil
                        #add any missing self.%s = nil calls
                        #convert autoreleases to releases
                        pass
        #in the old system we don't audit ivars, because Drew doesn't care

        return file

    def __str__(self):
        if self.property:
            if self.readonly:
                memory = "readonly, %s" % self.memory
            else:
                memory = self.memory
            return "@property (%s, %s) %s%s%s %s%s;" % (self.atomicity, memory, self.block, self.iboutlet, self.type, self.pointer, self.name)
        else:
            #atomicty is hacked for ivars to contain the leading whitespace
            return "%s%s %s%s%s &s%s;" % (self.atomicity, self.memory, self.block, self.iboutlet, self.type, self.pointer, self.name)