@interface bad : NSObject
{
    BOOL state;
    NSArray *foo;
    NSArray *foo2;
    NSError *error;
}

@property (nonatomic, readonly) __block int lineNum;
@property (atomic, retain) NSMutableString *temp;
@property (atomic, copy) __block NSArray *foo;
@property (atomic, copy) IBOutlet NSString *text;
@end
