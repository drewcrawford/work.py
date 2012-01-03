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

- (void)enqueue:(NSDictionary *)myDict withClean:(NSDictionary *)cleanDict {
#define LOG(BACKEND) BOOL result = NO;\
while (!result) {\
    result = [backend log:([backend wantsCleanDict])?cleanDict:myDict];\
}
    for(id <JucheBackend> backend in backends) {
        if (![backend wantsLogSync]) continue;
            LOG(backend);
        }
        dispatch_async(myQueue, ^{
            for (id <JucheBackend> backend in backends) {
                if ([backend wantsLogSync]) continue;
                LOG(backend);
            }
        });
}
@end
