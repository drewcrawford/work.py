try:
	import BeautifulSoup
except:
	print "It appears you don't have beautiful soup installed.  Want to give that a try? y/n"
	if (raw_input()=="y"):
		import os
		os.system("curl -O http://www.crummy.com/software/BeautifulSoup/download/3.x/BeautifulSoup-3.2.0.tar.gz")
		os.system("tar xfvj BeautifulSoup*")
		os.system("cd BeautifulSoup-3.2.0/ && python setup.py install")
		os.system("rm -rf BeautifulSoup*")

from distutils.core import setup
setup(name='work.py',version='1.0',
py_modules=['fogbugz','gitConnect','fogbugzConnect'],
scripts=['work.py']
)
