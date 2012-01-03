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
    
    
    for(int i = 0; i < 3; i++) {
	    REVOLT(@"i",[NSString stringWithFormat:@"%d",i],^{
            //each log statement in this block shows the contents of the i variable
		    JUCHE(JINFO,@"Inner loop"); 
	    });
    }
}

@end
