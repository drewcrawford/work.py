//
//  UnifiedQueue.m
//  JucheLog
//
//  Created by Drew Crawford on 12/30/11.
//  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
//

#import "UnifiedQueue.h"
#import "JucheBackend.h"
#import "NSLogBackend.h"
static UnifiedQueue *sharedQueue;
@interface UnifiedQueue () {
    NSMutableArray *backends;
    dispatch_queue_t myQueue;
}
@end
@implementation UnifiedQueue

+ (UnifiedQueue*) sharedQueue {
    if (sharedQueue) return sharedQueue;
    sharedQueue = [[UnifiedQueue alloc] init];
    return sharedQueue;
}
- (id) init {
    if (self = [super init]) {
        myQueue = dispatch_queue_create("JucheLog", DISPATCH_QUEUE_SERIAL);
        backends = [[NSMutableArray alloc] init];
        [backends addObject:[[NSLogBackend alloc] init]];
    }
    return self;
}
- (void) dealloc {
    dispatch_release(myQueue);
}

- (void) registerBackend:(id<JucheBackend>) backend {
    [backends addObject:backend];
}
+ (NSDictionary*) fixDictFor:(id<JucheBackend>) backend inDict:(NSDictionary*) d {
    if ([backend wantsLocalOnly]) {
        NSArray *reserved = [NSArray arrayWithObjects:@"app",@"version",@"who", nil];
        NSMutableDictionary *result = [[NSMutableDictionary alloc] init];
        for (NSString *key in d.allKeys) {
            if (![reserved containsObject:key]) {
                [result setObject:[d objectForKey:key] forKey:key];
            }
        }
        return result;
    }
    else return d;
}

- (void)enqueue:(NSDictionary *)myDict {
    for(id <JucheBackend> backend in backends) {
        if (![backend wantsLogSync]) continue;
        BOOL result = NO;
        while (!result) {
            result = [backend log:[UnifiedQueue fixDictFor:backend inDict:myDict]];
        }
    }
        dispatch_async(myQueue, ^{
            for (id <JucheBackend> backend in backends) {
                if ([backend wantsLogSync]) continue;
                BOOL result = NO;
                while (!result) {
                    result = [backend log:[UnifiedQueue fixDictFor:backend inDict:myDict]];
                }
            }
        });
}
@end
