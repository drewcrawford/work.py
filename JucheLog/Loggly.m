//
//  Loggly.m
//  JucheLog
//
//  Created by Drew Crawford on 12/30/11.
//  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
//

#import "Loggly.h"
#import "UnifiedQueue.h"
@implementation Loggly
@synthesize inputKey;

- (BOOL)wantsCleanDict { return NO; }

- (BOOL)wantsLogSync { return NO; }


+ (void) enableWithInputKey:(NSString*) key {
    Loggly *backend = [[Loggly alloc] init];
    backend.inputKey = key;
    [[UnifiedQueue sharedQueue] registerBackend:backend];
}
+ (NSString*) escape:(NSString*) me {
    NSMutableString *escaped = [[NSMutableString alloc] init];
    //http://www.google.com/codesearch#lcWXjIiPlFw/trunk/src/org/json/simple/JSONValue.java&q=escape%20package:http://json-simple%5C.googlecode%5C.com&l=211
    NSArray *reserved = [NSArray arrayWithObjects:@"'",@"\"",@"\\",@"\b",@"\f",@"\n",@"\r",@"\t",@"/", nil];
    for (int i = 0; i < me.length; i++) {
        unichar c = [me characterAtIndex:i];
        NSString *c_str = [NSString stringWithCharacters:&c length:1];
        if ([reserved containsObject:c_str]) [escaped appendString:@"\\"];
        [escaped appendString:c_str];
    }
    return escaped;
}
+ (NSData*) crappyJSON:(NSDictionary*) dict {
    NSMutableString *str = [[NSMutableString alloc] init];
    [str appendString:@"{"];
    for(NSString *key in dict.allKeys) {
        [str appendFormat:@"'%@'='%@',",[self escape:key],[self escape:[dict objectForKey:key]]];
    }
    [str appendString:@"}"];
    return [str dataUsingEncoding:NSUTF8StringEncoding];
}
- (BOOL)log:(NSDictionary *)state {
    NSMutableURLRequest *req = [NSMutableURLRequest requestWithURL:[NSURL URLWithString:[NSString stringWithFormat:@"https://logs.loggly.com/inputs/%@",inputKey]]];
    [req addValue:@"application/json" forHTTPHeaderField:@"content-type"];
    [req setHTTPMethod:@"POST"];
    [req setHTTPBody:[Loggly crappyJSON:state]];
    NSHTTPURLResponse *response = nil;
    NSError *err = nil;
    NSData *data = [NSURLConnection sendSynchronousRequest:req returningResponse:&response error:&err];
    if (err) {
        NSLog(@"Error in Loggly: %@",err);
        return NO;
    }
    else {
        NSString *responseString = [[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding];
        if ([responseString isEqualToString:@"{\"response\":\"ok\"}"]) return YES;
        return NO;
    }
    
}

@end
