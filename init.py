import os
import os.path
import sys
import cgi
import cStringIO
import hashlib
import base64

# Observed that we don't seem to have a sane umask, URL files are
# coming out with mode 666, kinda unexpected.
os.umask(022)

# Get config from the environment
URL_STEM  = os.environ.get('URL_STEM')
URL_STORE = os.environ.get('URL_STORE')

URL_ENTRY_FORM = """
            <form method="get">
            <label for="url">URL to shorten</label>
            <input type="text" name="new_url" size="60" id="url" accesskey="u" />
            <input type="submit" value="Shorten!" accesskey="s" />
            </form>
"""

class http_response(object):
    def __init__(self, environ, start_response):
        self.buffer = cStringIO.StringIO()
        self.environ = environ
        self.start_response = start_response
        self.status = '200 OK'
        self.headers = [('Content-Type', 'text/html; charset=utf-8'), ('P3P', '''policyref="/w3c/p3p.xml", CP="NOI NOR CURa OUR"''')]

    def write(self, data):
        self.buffer.write(data)

    def finalise(self):
        """
        Closes the output buffer, writes the correct header/s and returns
        something suitable for returning from the top-level application() call
        """
        self.value = self.buffer.getvalue()
        self.buffer.close()
        self.headers.append(('Content-Length', str(len(self.value))))
        self.start_response(self.status, self.headers)
        return [self.value]

    def redirect(self, url):
        self.buffer.close()
        self.status = '302 Found'
        self.headers = [('Content-Type', 'text/html'), ('Location', url)]
        self.start_response(self.status, self.headers)
        return ['redirecting']

    def boom(self, msg):
        self.status = '500 Server side error'
        print >>self.buffer, "Critical error, HTTP status 500"
        print >>self.buffer, str(msg)
        return self.finalise()


class hash_machine(object):
    class NoMoreRotationException(Exception):
        pass
    def __init__(self, raw_data):
        self.full_hash = base64.b32encode(hashlib.sha1(raw_data).digest())
        self.hash_len = len(self.full_hash)
        self.rotation_counter = 0
    def get_hash(self):
        if self.rotation_counter < self.hash_len:
            mini_hash = (self.full_hash[self.rotation_counter:] + self.full_hash[:self.rotation_counter])[:6]
            self.rotation_counter += 1
            return mini_hash
        else:
            raise self.NoMoreRotationException


def application(environ, start_response):
    if URL_STORE is None:
        return output.boom("The URL_STORE environment variable is not set, cannot run.")

    # Setup our output
    output = http_response(environ, start_response)
    sys.stdout = output
    wsgi_errors = environ['wsgi.errors']

    # Get all our form input
    form = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)
    SHORT = str(form.getfirst("short", ''))
    NEW = str(form.getfirst("new_url", ''))

    if SHORT:
        URL_FILE = os.path.join(URL_STORE, SHORT)
        URL = ''

        if os.path.exists(URL_FILE):
            f = open(URL_FILE)
            URL = f.readlines()
            f.close()
            if len(URL) < 1:
                return output.boom("URL file %s doesn't seem to have a URL in it!" % URL_FILE)
            return output.redirect(URL[0])
        else:
            return output.boom("URL file %s doesn't exist" % URL_FILE)

    elif NEW:
        print '''Your URL is <a href="%s">%s</a><br />''' % (NEW, NEW)
        hasher = hash_machine(NEW)

        while True:
            try:
                h = hasher.get_hash()
            except NoMoreRotationException:
                return output.boom("Damn, couldn't get a hash for that URL for some reason")

            print "<p>Mini hash is %s</p>" % h
            URL_FILE = os.path.join(URL_STORE, h)


            if not os.path.exists(URL_FILE):
                print "<p>%s doesn't exist yet, great!</p>" % URL_FILE
                f = open(URL_FILE, 'w')
                f.write(NEW)
                f.close()
                URL = URL_STEM + h
                print "<p>Okay, here's your URL:</p>"
                print '''<p><a href="%s">%s</a></p>''' % (URL, URL)
                print '''<p>%s</p>''' % URL
                print "<hr /><p>Shorten again?<br />" + URL_ENTRY_FORM + "</p>"
                return output.finalise()
            else:
                print "<p>Hmm, that one already exists, let's see if it's the same</p>"
                f = open(URL_FILE)
                URL = f.readlines()
                f.close()

                if len(URL) < 1:
                    print "<p>URL file %s doesn't seem to have a URL in it, we should use it</p>" % URL_FILE
                    f = open(URL_FILE, 'w')
                    f.write(NEW)
                    f.close()
                    URL = URL_STEM + h
                    print "<p>Okay, here's your URL:</p>"
                    print '''<p><a href="%s">%s</a></p>''' % (URL, URL)
                    print '''<p>%s</p>''' % URL
                    print "<hr /><p>Shorten again?<br />" + URL_ENTRY_FORM + "</p>"
                    return output.finalise()

                CURRENT_URL = URL[0]
                if CURRENT_URL == NEW:
                    URL = URL_STEM + h
                    print "<p>Okay, no problem here's your URL:</p>"
                    print '''<p><a href="%s">%s</a></p>''' % (URL, URL)
                    print '''<p>%s</p>''' % URL
                    print "<hr /><p>Shorten again?<br />" + URL_ENTRY_FORM + "</p>"
                    return output.finalise()

                print "<p>Damn, a collision, let's try again...</p>"


        # Should never get here? Probably proveable.
        return output.finalise()

    else:
        print """<p>
            <center>
            <img src="/static/poliwag.jpg" width="260" height="240" /><br />
            Sorry, nothing to see here<br />
            <hr />""" + URL_ENTRY_FORM + """
            </center>
            <div style="color: silver;">
            <small><pre>javascript:var%20u='http://lzma.so/?new_url='+encodeURIComponent(document.location.href);a=function(){if(!window.open(u))document.location.href=u;};if(/Firefox/.test(navigator.userAgent))setTimeout(a,0);else%20a();void(0);</pre></small>
            </div>
        </p>"""

        # Dead code, we don't want to enumerate all the short URLs
        return output.finalise()
        URL_DIR = URL_FILE = URL_STORE
        print "<ul>"
        for FILE in os.listdir(URL_DIR):
            print '''<li><a href="%s">%s</a></li>''' % (FILE, FILE)
        print "</ul>"
        return output.finalise()



from paste.exceptions.errormiddleware import ErrorMiddleware
application = ErrorMiddleware(application, debug=True)
