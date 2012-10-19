#JUCHELOG
![JUCHE](http://github.com/drewcrawford/JucheLog/raw/master/img/juche1.jpg)

Democratic People's Juche Logger

##What is JucheLog?
JucheLog is a minimalist, cross-platform logging library inspired by Paul Querna's [Write Logs for Machines, use JSON](http://journal.paul.querna.org/articles/2011/12/26/log-for-machines-in-json/) article.  Current support for Python and Objective-C.

##Why should I use JucheLog?
1.  You are getting lost in your own logs and are writing programs to search through your logs for relevant information, or have considered writing such programs, but it's not quite worth it.
2.  You want to be able to recursively nest or "code-fold" your logs for readability
3. Your logs often do not have the right information, causing you to insert more log statements and get longer logs that are more difficult to read
4. Your code is sprinkled with log("BEGIN X") and log("END X")
5. You log state information, like usernames, system configuration, the current task, and so on, but the state is often logged many lines before or after the failure or the line of interest, causing you to have to jump around the log file to understand the failure.
6. You wish you could pipe log events from your tens of thousands of application customers or your beowulf cluster over a network to a single server for remote debugging of customer issues, but the network traffic would be way too much bandwidth for your tiny server, and it's too much work to try and prune it
7. You write things like `if (i%1000) log("debug")`
8. You have realized that effectively the difference between a debug log, an error log, and an analytics system are essentially volume.  All three log events, but some log more than others.  You wish you could do the work once and somehow get the benefit of all three.
9. You are frightened by the complexity of other logging systems and you just want to run a find-replace on your project to solve all your problems, and *maybe* learn a new function call or two.

##Using JucheLog

It's simple!

```python
import juchelog
juche.info("Hello world!")
```

or with Objective-C:

```objc
#include <JucheLog/JucheLog.h>
JUCHE(JINFO,@"Hello world!");
```


You can add network logging with just one line:

```python
__builtins__.JUCHE_KEY="<YOUR_KEY>" #python
```

```objc
[Loggly enableWithInputKey:@"YOUR_KEY>"] //objc
```

Now all your logs talk to Loggly.

But that's just the start of the power of Juche!  One of the important principles is that you can bundle *context* into your log messages.  Check out this awesome example:

```objc
	for(int i = 0; i < 3; i++) {
		    [JucheLog revolt:@"i",[NSString stringWithFormat:@"%d",i],^{
			    JUCHE(JINFO,@"My awesome loop"); 
		    }];
	   }
```

Or in python:

```python
	for i in range(0,3):
		with juche.revolution(i=i):
			juche.info("My awesome loop")
```
Both of these programs output

	|  [INFO] 19:12:11 My awesome loop i=0  juchelog.py:142
	|  [INFO] 19:12:11 My awesome loop i=1  juchelog.py:142
	|  [INFO] 19:12:11 My awesome loop i=2  juchelog.py:142

The context, i=%d, is propagated to the log statements inside the block, without you having to include them explicitly in each log statement.  Context is automatically nested for you, so by adding context to an outer block, you add the context to each encapsulated log message.

Context logging turns out to be pretty useful.  In fact, only a tiny part of the complete context is output to the terminal.  Here is the full context information that is sent up to Loggly:

	{"threadName": "MainThread", "relativeCreated": 205.98006248474121, "process": 29823, "module": "juchelog", "funcName": "<module>", "message": "Inner loop!", "filename": "juchelog.py", "levelno": 20, "processName": "MainProcess", "lineno": 150, "asctime": "19:12:11", "msg": "Inner loop!", "args": [], "exc_text": "org.json.JSONObject$Null:null", "name": "JUCHE", "thread": 140735208573280, "created": 1325553131.79333, "j": 1, "msecs": 793.32995414733887, "pathname": "JucheLog/juchelog.py", "exc_info": "org.json.JSONObject$Null:null", "levelname": "INFO"}
	{"threadName": "MainThread", "relativeCreated": 205.98006248474121, "process": 29823, "module": "juchelog", "funcName": "<module>", "message": "Inner loop!", "filename": "juchelog.py", "levelno": 20, "processName": "MainProcess", "lineno": 150, "asctime": "19:12:11", "msg": "Inner loop!", "args": [], "exc_text": "org.json.JSONObject$Null:null", "name": "JUCHE", "thread": 140735208573280, "created": 1325553131.79333, "j": 1, "msecs": 793.32995414733887, "pathname": "JucheLog/juchelog.py", "exc_info": "org.json.JSONObject$Null:null", "levelname": "INFO"}
	{"relativeCreated": 194.17119026184082, "process": 29823, "module": "juchelog", "funcName": "<module>", "message": "My awesome loop", "filename": "juchelog.py", "levelno": 20, "processName": "MainProcess", "lineno": 142, "asctime": "19:12:11", "msg": "My awesome loop", "args": [], "exc_text": "org.json.JSONObject$Null:null", "name": "JUCHE", "thread": 140735208573280, "created": 1325553131.7815211, "i": 0, "threadName": "MainThread", "msecs": 781.52108192443848, "pathname": "JucheLog/juchelog.py", "exc_info": "org.json.JSONObject$Null:null", "levelname": "INFO"}
	
This includes such elements as lines of code, time, function calls, paths, threading info, and much more.  In Objective-C, this packet contains other helpful debugging information, like unique identifiers and app bundle IDs.  All of this is fully queryable on Loggly's hadoop cluster.	This lets you do crazy things like profile your code after-the-fact, debug issues in production, and use debug logs as analytics.

But that's just the beginning of the power of JucheLog!  Try this example:

```python
	for i in range(0,3):
		with juche.revolution(i=i,eternal_president="kim-il-sun"):
			juche.info("Outer loop!")
			for j in range(0,2):
				with juche.revolution(j=j):
					juche.info("Inner loop!")
```

This program will output:

	|  [INFO] 19:12:11 Outer loop! i=0 eternal_president=kim-il-sun  juchelog.py:147
	|  |  [INFO] 19:12:11 Inner loop! j=0  juchelog.py:150
	|  |  [INFO] 19:12:11 Inner loop! j=1  juchelog.py:150
	|  [INFO] 19:12:11 Outer loop! i=1 eternal_president=kim-il-sun  juchelog.py:147
	|  |  [INFO] 19:12:11 Inner loop! j=0  juchelog.py:150
	|  |  [INFO] 19:12:11 Inner loop! j=1  juchelog.py:150
	|  [INFO] 19:12:11 Outer loop! i=2 eternal_president=kim-il-sun  juchelog.py:147
	|  |  [INFO] 19:12:11 Inner loop! j=0  juchelog.py:150
	|  |  [INFO] 19:12:11 Inner loop! j=1  juchelog.py:150

Some things to note about this:

1.  Indented, nested, threaded, pretty log statements, with zero effort on your part
2. You get the data from *only the most recent call to revolution* in-line with your log statement as Terminal output.  This is just to make the output manageable.  
3. But the *complete context* gets sent over the wire to Loggly, where you can query it.  So in loggly, you will see something like this:

```
{"function": "__block_global_0", "who": "G88014V4XYK", "indent": "2", "thread": "main", "eternal_president": "kim-il-sun", "i": "2", "app": "com.dca.JucheLogTestMac", "j": "2", "version": "1", "file": "JucheLogTests.m", "msg": "Inner loop!", "line": "44", "level": "info"}
```


Note that this includes not only the values for i, but also the values for j and eternal_president, not to mention other helpful context information not printed to stderr.

### Projected Cost

JucheLog is written and maintained by two developers at DrewCrawfordApps LLC, an iPhone and iPad consulting company.  JucheLog is the result of approximately 15 hours of work, valued at $1875 at current market rates, and is provided to you at no charge.  If this project is of use to you please consider us for your next Objective-C project.

