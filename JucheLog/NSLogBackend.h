//
//  NSLogBackend.h
//  JucheLog
//
//  Created by Drew Crawford on 12/30/11.
//  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "JucheBackend.h"
@interface NSLogBackend : NSObject <JucheBackend>
- (BOOL)log:(NSDictionary *)state;
- (BOOL) wantsLogSync;
@end
