import logging.handlers
import logging
import urllib2
from json import dumps
from urllib import quote_plus
import os


def post_to_endpoint(endpoint, message):
	r = urllib2.Request(endpoint,data=message,headers={"content-type":"application/json"})
	response = urllib2.urlopen(r)
	

class JucheHandler (logging.Handler):

	def __init__(self,  key=''):
		super(JucheHandler,self).__init__()
		self.key = key
		secure = False
		protocol = secure and 'https' or 'http'
		self.endpoint = "%s://%s/inputs/%s" % (protocol, "logs.loggly.com", key)

	def emit(self, record):
		if isinstance(record.msg, (list, dict)):
			record.msg = dumps(record.msg, cls=self.json_class, default=str)
		post_to_endpoint(self.endpoint, dumps(record.__dict__))

class JucheRecord(logging.LogRecord):
	def __init__(self,*args,**kwargs):
		super(JucheRecord,self).__init__(*args,**kwargs)

class JucheLogger(logging.getLoggerClass()):
	stack = [{}]
	def __init__(self,name):
		super(JucheLogger,self).__init__(name)
		self.stack = [{"indent":0,"who":os.uname()[1]}]
		jucheHandler = JucheHandler(key="dbd1f4d5-5c41-4dc7-8803-47666d46e01d")
		self.setLevel(logging.DEBUG)
		jucheHandler.setLevel(logging.INFO)
		self.addHandler(jucheHandler)
		basicFormatter = IndentFormatter("[%(levelname)s]%(indent)s%(message)s")
		handler = logging.StreamHandler()
		handler.setFormatter(basicFormatter)
		self.addHandler(handler)
	def currentState(self):
		return self.stack[-1]
	
	def push(self):
		self.stack.append(dict(self.currentState()))
	def pop(self):
		self.stack = self.stack[:-1]
	def set(self,key,val):
		self.stack[-1][key]=val

	def indent(self):
		self.set("indent",self.currentState()["indent"]+1)
	def dedent(self):
		self.set("indent",self.currentState()["indent"]-1)
	
	def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None):
		record =  JucheRecord(name, level, fn, lno, msg, args, exc_info, func)
		for (key,val) in self.currentState().iteritems():
			record.__setattr__(key,val)
		record.indent = self.currentState()["indent"]
		return record

class IndentFormatter(logging.Formatter):
    def __init__( self, fmt=None, datefmt=None ):
        logging.Formatter.__init__(self, fmt, datefmt)
    def format( self, rec ):
        rec.indent = '  '*(rec.indent)
        out = logging.Formatter.format(self, rec)
        del rec.indent
        return out

logging.setLoggerClass(JucheLogger)
