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
    JUCHE(JINFO, @"This is at indent level 0");
    [JucheLog indent];
    JUCHE(JINFO, @"This is at indent level 1");
    [JucheLog indent];
    JUCHE(JINFO, @"This is at indent level 2");
    [JucheLog dedent];
    JUCHE(JWARNING,@"This is at indent level 1");
    [JucheLog dedent];
    JUCHE(JWARNING,@"This is at indent level 0");
}

@end
