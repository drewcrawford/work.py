try:
	import lint
except:
	print "It appears you don't have CodeLint installed.  Want to give that a try? y/n"
	if (raw_input()=="y"):
		import os
		os.system("curl -L https://github.com/bionoren/CodeLint/tarball/master > lint.tar.gz")
		os.system("tar xfv lint.tar.gz")
		os.system("rm -rf lint.tar.gz")
		os.system("cd bionoren-CodeLint-* && python setup.py install")
		os.system("rm -rf bionoren-CodeLint-*")

try:
	import BeautifulSoup
except:
	print "It appears you don't have beautiful soup installed.  Want to give that a try? y/n"
	if (raw_input()=="y"):
		import os
		os.system("curl -O http://www.crummy.com/software/BeautifulSoup/bs3/download//3.x/BeautifulSoup-3.2.0.tar.gz")
		os.system("tar xfv BeautifulSoup*")
		os.system("cd BeautifulSoup-3.2.0/ && python setup.py install")
		os.system("rm -rf BeautifulSoup*")
try:
	import keyring
except:
	print "It appears you don't have keyring installed.  Want to give that a try? y/n"
	if (raw_input()=="y"):
		import os
		os.system("curl -O http://pypi.python.org/packages/source/k/keyring/keyring-0.5.1.tar.gz")
		os.system("tar -xvf keyring-0.5.1.tar.gz")
		os.system("cd keyring-0.5.1 && python setup.py install")
		os.system("rm -rf keyring-0.5*")

from distutils.core import setup
from os import system
system("git rev-parse HEAD > /usr/local/etc/.work.version")
setup(name='work.py',version='1.0',
py_modules=['fogbugz','gitConnect','fogbugzConnect','gitHubConnect','JucheLog.juchelog'],
scripts=['work.py'],
data_files = [('media',['media/dundundun.aiff','media/hooray.aiff','media/longcheer.aiff','media/ohno.aiff'])]
)
