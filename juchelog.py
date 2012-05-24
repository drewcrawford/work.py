import logging.handlers
import logging
import urllib2
from json import dumps
from urllib import quote_plus
import os
from contextlib import contextmanager
import threading
import textwrap
import sys

def undefined_behavior():
	print """
	               .,-:;//;:=,
	           . :H@@@MM@M#H/.,+%%;,
	        ,/X+ +M@@M@MM%%=,-%%HMMM@X/,
	      -+@MM; $M@@MH+-,;XMMMM@MMMM@+-
	     ;@M@@M- XM@X;. -+XXXXXHHH@M@M#@/.
	   ,%%MM@@MH ,@%%=            .---=-=:=,.
	   =@#@@@MX .,              -%%HX$$%%%%%%+;
	  =-./@M@M$                  .;@MMMM@MM:
	  X@/ -$MM/                    .+MM@@@M$
	 ,@M@H: :@:                    . =X#@@@@-
	 ,@@@MMX, .                    /H- ;@M@M=
	 .H@@@@M@+,                    %%MM+..%%#$.
	  /MMMM@MMH/.                  XM@MH; =;
	   /%%+%%$XHH@$=              , .H@@@@MX,
	    .=--------.           -%%H.,@@@@@MX,
	    .%%MM@@@HHHXX$$$%%+- .:$MMX =M@@MM%%.
	      =XMMM@MM@MM#H;,-+HMM@M+ /MMMX=
	        =%%@M@M#@$-.=$@MM@@@M; %%M%%=
	 	 ,:+$+-,/H#MMMMMMM@= =,
	                =++%%%%%%%%+/:-.
	 ........................................
	 ....... Aperture Laboratories(R)  ......
	 ........................................"""

	raise Exception("Direct manipulation of the stack while it is automatically managed is undefined.  Consider using managed mode or unmanaging the stack prior to direct manipulation.")

def post_async(endpoint,message):
	r = urllib2.Request(endpoint,data=message,headers={"content-type":"application/json"})
	try:
		data = urllib2.urlopen(r)
		response = data.read()
		if response != '{"response": "ok"}':
			print "JUCHE FAIL",response
	except e as Exception:
		print "juche fail",e
	
def post_to_endpoint(endpoint, message):
	t = threading.Thread(target=post_async,args=[endpoint,message])
	t.start()

def non_logging_raw():
	import traceback
	stack = traceback.extract_stack()
	arr = []
	for item in stack:
		if item[0].find("logging/__init__.py")==-1: arr.append(item)
		else: break
	return arr
def non_logging_exc():
	import traceback
	return "".join(traceback.format_list(non_logging_raw()))

def greatest_common_traceback(tb1,tb2):
	min_tb = min([len(tb1),len(tb2)])
	common = []
	for i in range(0,min_tb):
		a = tb1[i]
		b = tb2[i]
		if (a==b):
			common.append(a)
		else:
			break
	return common






class LogglyHandler (logging.Handler):

	def __init__(self,  key=''):
		super(LogglyHandler,self).__init__()
		self.key = key
		secure = False
		protocol = secure and 'https' or 'http'
		self.endpoint = "%s://%s/inputs/%s" % (protocol, "logs.loggly.com", key)

	def emit(self, record):
		if record.message=="JUCHE_REVOLUTION": return
		record = dict(record.__dict__)
		del record["JUCHE_IS_AWESOME"]
		def json_format(obj):
			import traceback
			if isinstance(obj,traceback.types.TracebackType):
				return traceback.extract_tb(obj)
			if isinstance(obj,type):
				return repr(obj)
			if isinstance(obj,Exception):
				return repr(obj)
			import datetime
			if isinstance(obj,datetime.datetime):
				return repr(obj)
			return repr(obj)
		post_to_endpoint(self.endpoint, dumps(record,default=json_format))

class JucheRecord(logging.LogRecord):
	def __init__(self,*args,**kwargs):
		super(JucheRecord,self).__init__(*args,**kwargs)

class JucheLogger(logging.Logger):
	stack = [{}]
	managed = False #Some operations are undefined if the stack is managed

	def __init__(self,name):
		#print "juche init with name %s" % name
		super(JucheLogger,self).__init__(name)
		self.stack = [{"indent":0,"who":os.uname()[1]}]
		self.clean_stack = list(self.stack)
		self.setLevel(logging.DEBUG)

		#set auto_stack to default level
		self.unmanage(extracted_stack=non_logging_raw()) 
		self.manage()
		#print "initing stack to %s" % self.stack

		basicFormatter = IndentFormatter("%(indent)s[%(levelname)s] %(asctime)s %(message)s %(JUCHE_IS_AWESOME)s %(filename)s:%(lineno)s",datefmt='%H:%M:%S')
		handler = logging.StreamHandler()
		handler.setFormatter(basicFormatter)
		handler.setLevel(logging.DEBUG)
		self.addHandler(handler)
		try:
			jucheHandler = LogglyHandler(key=globals()["__builtins__"].LOGGLY_KEY)
			jucheHandler.setLevel(logging.INFO)
			self.addHandler(jucheHandler)
		except:
			self.warning("__builtins__.LOGGLY_KEY is not set up, network logging is disabled.")

	def _log(self,*args,**kwargs):
		
		if self.managed and not kwargs.has_key("DO_NOT_UNMANAGE"):
			self.unmanage(extracted_stack=non_logging_raw())
			self.manage()
		if kwargs.has_key("DO_NOT_UNMANAGE"): del kwargs["DO_NOT_UNMANAGE"]
		super(JucheLogger,self)._log(*args,**kwargs)

	def currentState(self):
		return self.stack[-1]

	def push(self,ignore_undefined_behavior_check=False):
		if self.managed and not ignore_undefined_behavior_check: undefined_behavior()
		#print "push"
		self.stack.append(dict(self.currentState()))
		self.clean_stack.append({})

	def pop(self,ignore_undefined_behavior_check=False):
		if self.managed and not ignore_undefined_behavior_check: undefined_behavior()

		#print "pop"
		self.stack = self.stack[:-1]
		self.clean_stack = self.clean_stack[:-1]
	def set(self,tuples):
		#print "setting %s"%tuples
		for (key,val) in tuples:
			try:
				dumps(val)
			except:
				val = repr(val)
			self.stack[-1][key]=val
			self.clean_stack[-1][key]=val

	def unmanage(self,extracted_stack=None):
		import traceback
		if not extracted_stack:
			extracted_stack = traceback.extract_stack()[:-1]
		
		stack = traceback.format_list(extracted_stack)
		while True:
			state = self.currentState()
			if not state.has_key("auto_stack"): 
				self.push(ignore_undefined_behavior_check=True)
				self.set([("auto_stack",stack)])
				break
			state_stack = state["auto_stack"]
			common = greatest_common_traceback(stack,state_stack)
			if len(state_stack) > len(stack): #The current managed stack needs to be popped
				#print "case 1"#,"".join(stack),"WOAH","".join(state_stack)
				self.pop(ignore_undefined_behavior_check=True)

			elif len(stack)==len(state_stack) and stack[:-1]==common:
				#print "case 2"
				break
			elif not state == self.currentState(): #maybe we need to search further?
				#print "case 3"
				pass
			else: #the current managed stack needs to be pushed
				#print "case 4" #,"".join(stack),"WOAH","".join(state_stack),len(stack),len(state_stack)
				self.push(ignore_undefined_behavior_check=True)
				self.indent()
				self.set([("auto_stack",stack)])
				break
		self.managed = False

	def manage(self):
		self.managed = True
				

			

	def dictate(self,**kwargs):
		#get the caller's filename and line number
		import traceback
		stack = traceback.extract_stack()
		stack_item = stack[-2]
		file_name = stack_item[0].split("/")[-1]
		line_no = stack_item[1]

		self.unmanage(extracted_stack=stack[:-1])
		for (key,val) in kwargs.iteritems():
			self.set([(key,val)])
		self.manage()

		juche.info("JUCHE_REVOLUTION",extra={"lineno":line_no,"filename":file_name},DO_NOT_UNMANAGE=True)


	def indent(self):
		self.set([("indent",self.currentState()["indent"]+1)])

	def dedent(self):
		self.set([("indent",self.currentState()["indent"]-1)])
	def get_clean_stack_context(self,howMany):
		retdict = {}
		for i in range(1,howMany+1):
			if i < len(self.clean_stack): retdict.update(self.clean_stack[-1*i])
		return retdict

	def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None):
		record =  JucheRecord(name, level, fn, lno, msg, args, exc_info, func)
		if extra:
			for (key,val) in extra.iteritems():
				record.__setattr__(key,val)
		for (key,val) in self.currentState().iteritems():
			record.__setattr__(key,val)
		record.clean_stack_use = dict(self.get_clean_stack_context(1))
		record.indent = self.currentState()["indent"]
		return record

	@contextmanager
	def revolution(self,**kwargs):

		#We emit a JUCHE message, but we need to fake the file name and line no
		#because that message is emitted in this function, not in the caller.
		#what we really want to do is emit the caller's context.
		import traceback
		stack = traceback.extract_stack()
		stack_item = stack[-3]
		file_name = stack_item[0].split("/")[-1]
		line_no = stack_item[1]


		self.push()
		self.indent()
		for (key,val) in kwargs.iteritems():
			self.set([(key,val)])
		juche.info("JUCHE_REVOLUTION",extra={"lineno":line_no,"filename":file_name})

		try:
			yield
		except Exception as e:
			raise e
		finally:
			self.dedent()
			self.pop()


class IndentFormatter(logging.Formatter):
	def __init__( self, fmt=None, datefmt=None ):
		logging.Formatter.__init__(self, fmt, datefmt)


	def format( self, rec ):
		#we need to process exc_info first so that something else doesn't throw (i.e. JUCHE_WRAP not existing)
		tb = None
		ext = None


		if rec.__dict__["exc_info"] and len(rec.__dict__["exc_info"])==3: #exception
			import traceback
			tb = "\ntb: " + traceback.format_exc()
			ext = "\nfull traceback: " + non_logging_exc()
		dontcare = ["relativeCreated","process","levelno","who","exc_text","indent","name","thread","created","threadName","msecs","pathname",
		"exc_info","args","levelname","funcName","filename","module","msg","processName","lineno","message","asctime","auto_stack"]
		rec.indent = '|  '*(rec.indent)
		if "override_lineno" in rec.__dict__:
			rec.lineno = rec.override_lineno
		if "override_filename" in rec.__dict__:
			rec.filename = rec.override_filename

		out = ""

		for (key,val) in rec.clean_stack_use.iteritems():
			if key not in dontcare:
				#key = self.format_sub(key)
				#val = self.format_sub(val)
				out += "%s=%s " % (key,val)
		del rec.clean_stack_use
		rec.JUCHE_IS_AWESOME=out
		try:
			wrapwidth = JUCHE_WRAP
		except:
			wrapwidth = 9999999

		out = "%s " % super(IndentFormatter,self).format(rec)
		out = ("\n"+rec.indent+" ").join(textwrap.wrap(out,width=wrapwidth))
		del rec.indent

		if tb: #exception
			import traceback
			out += tb
			out += ext
			rec.__dict__["full_traceback"]=ext

		return out

if __name__=="__main__":
	__builtins__.LOGGLY_KEY="dbd1f4d5-5c41-4dc7-8803-47666d46e01d"
	#__builtins__.JUCHE_WRAP=60

logging.setLoggerClass(JucheLogger)
juche = logging.getLogger("JUCHE")
def testExcept():
	try:
		raise Exception("This is a sample exception!")
	except Exception as e:
		import traceback
		exc_type,exc_value,exc_traceback = sys.exc_info()
		traceback.print_exception(exc_type, exc_value, exc_traceback,
                                  limit=3, file=sys.stdout)

        juche.exception(e)
def testMoreExcept():
	testExcept()


import unittest

class TestSequence(unittest.TestCase):
	def setUp(self):
		pass
	def test_short(self):
		print "\n" #dot
		juche.info("test_short")
		for i in range(0,3):
			with juche.revolution(i=i):
				juche.info("My awesome loop")

	def test_long(self):
		juche.unmanage()
		print "\n"
		juche.info("test_long")
		for i in range(0,3):
			with juche.revolution(i=i,eternal_president="kim-il-sun"):
				juche.info("Outer loop!")
				for j in range(0,2):
					with juche.revolution(j=j):
						juche.info("Inner loop!")

	def test_auto(self):
		print "\n" #dot
		juche.info("test_auto")
		def inner_context():
			juche.info("This is recorded in the inner context")
			def more_inner_context():
				juche.info("this is in the inner, inner context")
			more_inner_context()
			juche.dictate(great_leader="kim-jong-il")
			more_inner_context()

		juche.dictate(eternal_president="kim-il-sun")
		juche.info("Test this base")
		inner_context()
		juche.info("After the inner context")


