@interface bad : NSViewController {
    BOOL state;
    NSArray *foo2;
    __weak NSError* error;
    __weak testWeak;
}

@property (nonatomic, readonly, weak) __block int lineNum;
@property (atomic, strong) NSMutableString* temp;
@property (atomic, strong) __block NSArray *foo;
@property (nonatomic, weak) IBOutlet NSString *text;
@property (atomic, strong) UIColor *crapColor;
@property (unsafe_unretained) UIColor *crapColor; 