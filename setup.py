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
try:
	import keyring
except:
	print "It appears you don't have keyring installed.  Want to give that a try? y/n"
	if (raw_input()=="y"):
		import os
		os.system("curl -O http://pypi.python.org/packages/source/k/keyring/keyring-0.5.1.tar.gz")
		os.system("tar -xzvf keyring-0.5.1.tar.gz")
		os.system("cd keyring-0.5.1 && python setup.py install")
		os.system("rm -rf keyring-0.5*")

from distutils.core import setup
setup(name='work.py',version='1.0',
py_modules=['fogbugz','gitConnect','fogbugzConnect'],
scripts=['work.py'],
data_files = [('media',['media/dundundun.aiff','media/hooray.aiff','media/longcheer.aiff','media/ohno.aiff'])]
)
