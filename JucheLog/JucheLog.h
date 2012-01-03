//
//  JucheLog.h
//  JucheLog
//
//  Created by Drew Crawford on 12/30/11.
//  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
//

#import <Foundation/Foundation.h>


//severity levels
#define JDEBUG @"debug"
#define JINFO @"info"
#define JWARNING @"warning"
#define JERROR @"error"
#define JFALL_OF_COMMUNISM @"fall_of_communism"

//juche macros
#define JUCHE_NSLOG(f,...) \
[JucheLog setKeysToValues:@"file",[[NSString stringWithUTF8String:__FILE__] lastPathComponent],@"line",[NSNumber numberWithInt:__LINE__],@"function",[NSString stringWithUTF8String:__PRETTY_FUNCTION__], nil];\
[JucheLog log:f,##__VA_ARGS__];\

#define JUCHE(JUCHE_SEVERITY,f,...) \
[JucheLog setKeysToValues:@"level",JUCHE_SEVERITY,nil];\
JUCHE_NSLOG(f,##__VA_ARGS__);\

#define JUCHE_SET1(JUCHE_SEVERITY,key,val,f,...) \
[JucheLog push];\
[JucheLog setKeysToValues:key,val,nil];\
JUCHE(JUCHE_SEVERITY,f,##__VA_ARGS__);\
[JucheLog pop]

#define JUCHE_IF(SYMBOL,SEVERITY,f,...) \
if (condition) JUCHE(SEVERITY,f,##__VA_ARGS__)






@interface JucheLog : NSObject
+ (void) push;
+ (void) pop;
+ (void) emit;
+ (void) indent;
+ (void) dedent;
+ (void) log:(NSString*) format, ... NS_FORMAT_FUNCTION(1,2);
+ (void) revolt:(id) firstKey, ...; //terminated by block
+ (void) setKeysToValues:(id) firstKey, ... NS_REQUIRES_NIL_TERMINATION;

@end
