//
//  JucheLogTests.m
//  JucheLogTests
//
//  Created by Drew Crawford on 12/30/11.
//  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
//

#import "JucheLogTests.h"
#import "JucheLog.h"
#import "Loggly.h"
@implementation JucheLogTests

- (void)setUp
{
    [super setUp];
    
    // Set-up code here.
}

- (void)tearDown
{
    // Tear-down code here.
    
    [super tearDown];
}

- (void)testLog
{
    [Loggly enableWithInputKey:@"dbd1f4d5-5c41-4dc7-8803-47666d46e01d"];
    [JucheLog indent];
    JUCHE_SET1(JINFO,@"Test key", @"Test value", @"Log this with the test key.");
    [JucheLog dedent];
    JUCHE(JWARNING,@"John had %f friends \' \" \\n", 3.5);
}

@end
