@interface bad () {
    NSMutableString *temp;
    int layer;
}
@property (nonatomic, readonly, __weak) NSMutableString *special;
@property (copy) id specialCopy;
@end

@implementation bad

@synthesize specialCopy;
@synthesize specialAssign, lineNum;
@synthesize temp;

@synthesize foo, text;

-(id)init {
    self = [super init];
    if(self) {
        foo = [[NSArray alloc] init];
        lineNum = 23;
    }
    return self;
}
-(void) viewDidLoad {
    self.special = @"this is text";
    if(self.foo.count == 3) {
        NSLog(@"This is a %@", foo);
    } else {
        self.foo = [NSArray arrayWithObject:@"bar"];
    }
}

+ (BOOL) uninterestingMethod1:(NSString*)str {
    for(int i = 0; i < 3; i++) {
        __weak int foo = i;
        int bar = i+1;
        __strong int baz = i-1;
        NSLog(@"%d != %d - %d", foo, bar, baz);
    }
    //if(lineNum)
    //{
    //  NSLog(@"here");
    //} else

    //{
    //  NSLog(@"there");
    //}
    NSLog("You're not here.");
    text = @"testblah";
    lineNum = 3;
    assert(YES);
    return NO;
}
- (void)setTemp:(NSMutableString*)newtemp {
    if(temp != newtemp) {
        temp = newtemp;
        lineNum++;
    }
}

-(void) dealloc {
    foo = nil;
}
@end