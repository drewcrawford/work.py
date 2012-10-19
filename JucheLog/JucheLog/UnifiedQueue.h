//
//  UnifiedQueue.h
//  JucheLog
//
//  Created by Drew Crawford on 12/30/11.
//  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "JucheBackend.h"
@interface UnifiedQueue : NSObject
+ (UnifiedQueue*) sharedQueue;
- (void) registerBackend:(id<JucheBackend>) backend;
- (void) enqueue:(NSDictionary*) fullDict withClean:(NSDictionary*) cleanDict;
@end
