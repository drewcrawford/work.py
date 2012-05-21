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

#include <sys/types.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <net/if_dl.h>
#include <ifaddrs.h>

static NSMutableDictionary *loggers;
@implementation JucheLog

+(NSString *)  uniqueID {
#if (defined(TARGET_OS_MAC) && ! defined(TARGET_IPHONE_SIMULATOR))
    NSString *serialNumberString = nil;
    io_struct_inband_t iokit_entry;
    uint32_t bufferSize = 4096; // this signals the longest entry we will take
    io_registry_entry_t ioRegistryRoot = IORegistryEntryFromPath(kIOMasterPortDefault, "IOService:/");
    IORegistryEntryGetProperty(ioRegistryRoot, kIOPlatformSerialNumberKey, iokit_entry, &bufferSize);
    serialNumberString = [NSString stringWithCString: iokit_entry encoding: NSASCIIStringEncoding];
    IOObjectRelease((unsigned int) iokit_entry);
    IOObjectRelease(ioRegistryRoot);
    return serialNumberString;
#else //ios
    struct ifaddrs * addrs;
    struct ifaddrs * cursor;
    const struct sockaddr_dl * dlAddr;
    const unsigned char* base;
    int i;
    
    NSMutableString *retVal=[NSMutableString stringWithCapacity:18];
    
    if (getifaddrs(&addrs) == 0) {
        cursor = addrs;
        while (cursor != 0 && ([retVal length] <17)) {
            if ( (cursor->ifa_addr->sa_family == AF_LINK)
                && (((const struct sockaddr_dl *) cursor->ifa_addr)->sdl_type == 0x6) && strcmp("lo0",  cursor->ifa_name)!=0 ) {
                dlAddr = (const struct sockaddr_dl *) cursor->ifa_addr;
                base = (const unsigned char*) &dlAddr->sdl_data[dlAddr->sdl_nlen];
                for (i = 0; i < dlAddr->sdl_alen; i++) {
                    [retVal appendFormat:@"%02X:", base[i]];
                }
                //delete the last :
                [retVal deleteCharactersInRange:NSMakeRange(([retVal length]-1), 1)];
            }
            cursor = cursor->ifa_next;
        }
        
        freeifaddrs(addrs);
    }    
    return retVal;
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
