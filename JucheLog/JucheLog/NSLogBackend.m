//
//  NSLogBackend.m
//  JucheLog
//
//  Created by Drew Crawford on 12/30/11.
//  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
//

#import "NSLogBackend.h"

static NSDateFormatter *dateFormatter;

@implementation NSLogBackend
- (BOOL)log:(NSDictionary *)state {
    NSArray *reserved = [NSArray arrayWithObjects:@"file",@"line",@"msg",@"indent",@"thread",@"function",@"level", nil];
    
    NSMutableString *string = [[NSMutableString alloc] init];
    
    int indent = [[state objectForKey:@"indent"] intValue];
    for(int i = 0; i < indent; i++) {
        [string appendString:@"|  "]; 
    }
    if (!dateFormatter) {
        dateFormatter = [[NSDateFormatter alloc] init];
        [dateFormatter setDateFormat:@"HH:mm:ss"];

    }

    //[[NSDate date] descriptionWithCalendarFormat:@"%H:%M:%S" timeZone:nil locale:nil]
    [string appendFormat:@"[%@] %@ %@ ",[state objectForKey:@"level"],[dateFormatter stringFromDate:[NSDate date]],[state objectForKey:@"msg"]];
    
    
    for(NSString *key in state.allKeys) {
        if ([reserved containsObject:key]) continue;
        NSString *value=[state objectForKey:key];
        [string appendFormat:@"%@=%@ ",key,value];
    }
    
    [string appendFormat:@"%@:%@",[state objectForKey:@"file"],[state objectForKey:@"line"]];
    
    fprintf(stderr,"%s\n",[string UTF8String]);
    return YES;
}

- (BOOL)wantsLogSync {
    return YES;
}
- (BOOL) wantsCleanDict {
    return YES;
}
@end
