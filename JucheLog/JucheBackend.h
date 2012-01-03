//
//  JucheBackend.h
//  JucheLog
//
//  Created by Drew Crawford on 12/30/11.
//  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
//

#import <Foundation/Foundation.h>

@protocol JucheBackend <NSObject>
- (BOOL) log:(NSDictionary*) state;

/**If yes, block the caller until the log has been processed.  If this is false, execution will return to the caller while the log is being processed.  You probably want this NO for NSLog, but YES for slow network-related things. */
- (BOOL) wantsLogSync;

/**Only pass recent values to this logger*/
- (BOOL) wantsCleanDict;
@end
