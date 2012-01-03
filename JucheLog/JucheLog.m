//
//  JucheLog.m
//  JucheLog
//
//  Created by Drew Crawford on 12/30/11.
//  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
//

#import "JucheLog.h"
#import "UnifiedQueue.h"
#import "JucheBackend.h"
@interface JucheLog () {
    NSMutableArray *stack;
    NSMutableArray *cleanStack;
}
@end

static NSMutableDictionary *loggers;
@implementation JucheLog

+ (NSString *)uniqueID
{
#ifdef TARGET_OS_MAC
    NSString *serialNumberString = nil;
    io_struct_inband_t iokit_entry;
    uint32_t bufferSize = 4096; // this signals the longest entry we will take
    io_registry_entry_t ioRegistryRoot = IORegistryEntryFromPath(kIOMasterPortDefault, "IOService:/");
    IORegistryEntryGetProperty(ioRegistryRoot, kIOPlatformSerialNumberKey, iokit_entry, &bufferSize);
    serialNumberString = [NSString stringWithCString: iokit_entry encoding: NSASCIIStringEncoding];
    IOObjectRelease((unsigned int) iokit_entry);
    IOObjectRelease(ioRegistryRoot);
    return serialNumberString;
#else
    return @"Not implemented";
#endif
}
+ (NSDictionary*) getTrueBundleDict {
    NSBundle *mainBundle = [NSBundle mainBundle];
    if ([[mainBundle objectForInfoDictionaryKey:@"CFBundleExecutablePath"] hasSuffix:@"otest"]) { //we are in some unit test
        for (NSBundle *bundle in [NSBundle allBundles]) {
            if (![[bundle objectForInfoDictionaryKey:@"CFBundleExecutablePath"] hasSuffix:@"otest"]) return [bundle infoDictionary];
        }
    }
    return [mainBundle infoDictionary];
}
+ (NSString*) app {
    return [[JucheLog getTrueBundleDict] objectForKey:@"CFBundleIdentifier"];
}
+ (NSString*) appversion {
    return [[JucheLog getTrueBundleDict] objectForKey:@"CFBundleVersion"];
}

+ (JucheLog*) arbitraryLogger {
    if (!loggers) loggers = [[NSMutableDictionary alloc] init];
    JucheLog *logger = [loggers objectForKey:[NSThread currentThread].name];
    if (!logger) {
        logger = [[JucheLog alloc] init];
        [loggers setObject:logger forKey:[NSThread currentThread].name];
    }
    return logger;
}



- (id) init {
    if (self = [super init]) {
        stack = [[NSMutableArray alloc] init];
        cleanStack = [[NSMutableArray alloc] init];
        NSMutableDictionary *state = [[NSMutableDictionary alloc] init];
        [stack addObject:state];
        NSMutableDictionary *cleanState = [[NSMutableDictionary alloc] init];
        [cleanStack addObject:cleanState];
        //configure state
        NSString *threadName = [NSThread currentThread].isMainThread?@"main":[NSThread currentThread].name;
        
        [state setObject:threadName forKey:@"thread"];
        [state setObject:[JucheLog uniqueID] forKey:@"who"];
        [state setObject:[JucheLog app] forKey:@"app"];
        [state setObject:[JucheLog appversion] forKey:@"version"];
        [state setObject:@"0" forKey:@"indent"];
    }
    return self;
}

- (NSMutableDictionary*) currentState {
    return [stack lastObject];
}

- (NSString*) description {
    return [NSString stringWithFormat:@"%@",self.currentState];
}

- (void) push {
    //NSLog(@"push");
    [stack addObject:[self.currentState mutableCopy]];
    [cleanStack addObject:[[NSMutableDictionary alloc] init]];
}
- (void) set:(id)key to:(id) obj {
   //NSLog(@"set %@ to %@",key,obj);
    NSString *desc = [obj description];
    NSString *ikey = [key description];
    [self.currentState setObject:desc forKey:ikey];
    [[cleanStack lastObject] setObject:desc forKey:ikey];
}
- (void) pop {
    //NSLog(@"pop");

    [stack removeLastObject];
    [cleanStack removeLastObject];
}
- (void) emit {
    [[UnifiedQueue sharedQueue] enqueue:self.currentState withClean:[cleanStack lastObject]];
}
+ (void) emit {
    [[JucheLog arbitraryLogger] emit];
}
+ (void) set:(id)key to:(id) obj {
    [[JucheLog arbitraryLogger] set:key to:obj];
}

+ (void) push {
    [[JucheLog arbitraryLogger] push];
}
+ (void) pop {
    [[JucheLog arbitraryLogger] pop];
}
+ (void)log:(NSString *)format, ... {
    JucheLog *logger = [JucheLog arbitraryLogger];
    va_list listOfArguments;
    va_start(listOfArguments, format);
    NSString *formattedString = [[NSString alloc] initWithFormat:format arguments:listOfArguments];
    va_end(listOfArguments);
    [logger set:@"msg" to:formattedString];
    [logger emit];
}
- (void) indent{
    int level = [[self.currentState objectForKey:@"indent"] intValue];
    [self set:@"indent"to:[NSString stringWithFormat:@"%d",level+1 ]];
}
- (void) dedent {
    int level = [[self.currentState objectForKey:@"indent"] intValue];
    [self set:@"indent"to:[NSString stringWithFormat:@"%d",level-1 ]];
}
+ (void) indent {
    [[JucheLog arbitraryLogger] indent];
}
+ (void) dedent {
    [[JucheLog arbitraryLogger] dedent];
}
+ (void) setKeysToValuesArray:(NSMutableArray*) nonsense {
    JucheLog *logger = [JucheLog arbitraryLogger];

    while (nonsense.count > 0) {
        id key = [nonsense objectAtIndex:0];
        [nonsense removeObject:key];
        id value = [nonsense objectAtIndex:0];
        [nonsense removeObject:value];
        [logger set:key to:value];
    }
}
+ (void) setKeysToValues:(id) firstKey, ... {
    
    //convert this nonsense to an NSMutableArray
    NSMutableArray *nonsense = [NSMutableArray array];
    [nonsense addObject:firstKey];
    va_list listOfArguments;
    va_start(listOfArguments,firstKey);
    while (firstKey) {
        [nonsense addObject:firstKey];
        firstKey = va_arg(listOfArguments, id);
    }
    va_end(listOfArguments);
    [self setKeysToValuesArray:nonsense];
    
    
}

+ (void)revolt:(id)firstKey, ... {
    //convert this nonsense to an NSMutableArray
    NSMutableArray *nonsense = [NSMutableArray array];
    [nonsense addObject:firstKey];
    va_list listOfArguments;
    va_start(listOfArguments,firstKey);
    while (YES) {
        [nonsense addObject:firstKey];
        firstKey = va_arg(listOfArguments, id);
        if (![firstKey isKindOfClass:[NSString class]]) break;
    }
    va_end(listOfArguments);
    [self push];
    [self indent];
    [self setKeysToValuesArray:nonsense];
    void (^myblock)() = firstKey;
    myblock();
    [self pop];
    
}




@end
