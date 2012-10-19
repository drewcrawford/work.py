//
//  Loggly.h
//  JucheLog
//
//  Created by Drew Crawford on 12/30/11.
//  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "JucheBackend.h"
@interface Loggly : NSObject <JucheBackend>
+ (void) enableWithInputKey:(NSString*) key;
@property (strong) NSString *inputKey;
@end
