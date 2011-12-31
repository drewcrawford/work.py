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
    NSArray *reserved = [NSArray arrayWithObjects:@"file",@"line",@"msg",@"indent", nil];
    NSArray *tail = [NSArray arrayWithObjects:@"file",@"line",@"msg", nil];
    
    NSMutableString *string = [[NSMutableString alloc] init];
    
    int indent = [[state objectForKey:@"indent"] intValue];
    for(int i = 0; i < indent; i++) {
        [string appendString:@"  "]; 
    }
    
    for(NSString *key in state.allKeys) {
        if ([reserved containsObject:key]) continue;
        NSString *value=[state objectForKey:key];
        [string appendFormat:@"%@=%@ ",key,value];
    }
    
    for(NSString *key in tail) {
        NSString *value = [state objectForKey:key];
        [string appendFormat:@"%@=%@ ",key,value];
    }
    NSLog(@"%@",string);
    return YES;
}

- (BOOL)wantsLogSync {
    return YES;
}
- (BOOL) wantsLocalOnly {
    return YES;
}
@end
