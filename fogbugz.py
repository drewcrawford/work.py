import urllib
import urllib2

import httplib, mimetypes

from BeautifulSoup import BeautifulSoup, CData

class FogBugzAPIError(Exception):
    pass

class FogBugzLogonError(FogBugzAPIError):
    pass

class FogBugzConnectionError(FogBugzAPIError):
    pass

class FogBugz:
    def __init__(self, url):
        self.__handlerCache = {}
        if not url.endswith('/'):
            url += '/'

        self._token = None
        self._opener = urllib2.build_opener()
        try:
            soup = BeautifulSoup(self._opener.open(url + 'api.xml'))
        except urllib2.URLError:
            raise FogBugzConnectionError("Library could not connect to the FogBugz API.  Either this installation of FogBugz does not support the API, or the url, %s, is incorrect." % (self._url,))
        self._url = url + soup.response.url.string
        self.currentFilter = None

    def logonTok(self,token):
        self._token = token
    def logon(self, username, password):
        """
        Logs the user on to FogBugz.

        Returns None for a successful login.
        """
        if self._token:
            self.logoff()
        try:
            response = self.__makerequest('logon', email=username, password=password)
        except FogBugzAPIError, e:
            raise FogBugzLogonError(e)
        
        self._token = response.token.string
        if type(self._token) == CData:
                self._token = self._token.encode('utf-8')
    def logoff(self):
        """
        Logs off the current user.
        """
        self.__makerequest('logoff')
        self._token = None

    def __makerequest(self, cmd, **kwargs):
        kwargs["cmd"] = cmd
        if self._token:
            kwargs["token"] = self._token
        try:
            if kwargs.has_key("files"):
                files = []
                fields = []
                fileCount = 0
                for key in kwargs:
                    if key.startswith("file"):
                        for filename in kwargs[key].keys():
                            fileCount += 1
                            files.append(("File%d" % fileCount,filename,kwargs[key][filename]))
                            
                            
                    else:
                        fields.append((key,str(kwargs[key])))
                fields.append(("nFileCount",str(fileCount)))
                from urlparse import urlsplit
                parsed = urlsplit(self._url)
                response = BeautifulSoup(self.post_multipart(parsed[1],parsed[2],fields,files)).response
                    
                
            else:
                response = BeautifulSoup(self._opener.open(self._url+urllib.urlencode(kwargs))).response
        except urllib2.URLError, e:
            raise FogBugzConnectionError(e)
        if response.error:
            print response
            print response.error
            raise FogBugzAPIError('Error Code %s: %s' % (response.error['code'], response.error.string))
        return response

    def __getattr__(self, name):
        """
        Handle all FogBugz API calls.

        >>> fb.logon(email@example.com, password)
        >>> response = fb.search(q="assignedto:email")
        """

        # Let's leave the private stuff to Python
        if name.startswith("__"):
            raise AttributeError("No such attribute '%s'" % name)

        if not self.__handlerCache.has_key(name):
            def handler(**kwargs):
                return self.__makerequest(name, **kwargs)
            self.__handlerCache[name] = handler
        return self.__handlerCache[name]


# http://code.activestate.com/recipes/146306-http-client-to-post-using-multipartform-data/
    def post_multipart(self,host, selector, fields, files):
        """
        Post fields and files to an http host as multipart/form-data.
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of (name, filename, value) elements for data to be uploaded as files
        Return the server's response page.
        """
        content_type, body = self.encode_multipart_formdata(fields, files)
        h = httplib.HTTPSConnection(host)
        headers = {
            'User-Agent': 'INSERT USERAGENTNAME',
            'Content-Type': content_type
            }
        h.request('POST', selector, body.decode('utf-8').encode('ascii', 'replace'), headers)
        res = h.getresponse()
        return res.read()
    
    def encode_multipart_formdata(self,fields, files):
        """
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of (name, filename, value) elements for data to be uploaded as files
        Return (content_type, body) ready for httplib.HTTP instance
        """
        BOUNDARY = 'ThIs_Is_tHe_bouNdaRY_$'
        CRLF = '\r\n'
        L = []
        #L.append('Content-Type: multipart/form-data; boundary=%s' % BOUNDARY)
        #L.append('')
        for (key, value) in fields:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            L.append(value)
        for (key, filename, value) in files:
            pass
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append('Content-Type: %s' % self.get_content_type(filename))
            L.append('')
            L.append(value)
        L.append('--' + BOUNDARY + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
        return content_type, body
    
    def get_content_type(self,filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
