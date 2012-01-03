//
//  NSLogBackend.m
//  JucheLog
//
//  Created by Drew Crawford on 12/30/11.
//  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
//

#import "NSLogBackend.h"

@implementation NSLogBackend
- (BOOL)log:(NSDictionary *)state {
    NSArray *reserved = [NSArray arrayWithObjects:@"file",@"line",@"msg",@"indent",@"thread",@"function", nil];
    
    NSMutableString *string = [[NSMutableString alloc] init];
    
    int indent = [[state objectForKey:@"indent"] intValue];
    for(int i = 0; i <= indent; i++) {
        [string appendString:@"|  "]; 
    }
    [string appendFormat:@"[%@] %@ %@ ",[state objectForKey:@"level"],[[NSDate date] descriptionWithCalendarFormat:@"%H:%M:%S" timeZone:nil locale:nil],[state objectForKey:@"msg"]];
    
    
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
- (BOOL) wantsLocalOnly {
    return YES;
}
@end
