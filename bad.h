@interface bad : NSObject {
    BOOL state;
    NSArray *foo;
}

@property __block NSArray *foo;
@property (atomic, copy) IBOutlet NSString *text;
@end
