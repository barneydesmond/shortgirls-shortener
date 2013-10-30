shortgirls.py
=============

A really simple URL shortening service written as a Python WSGI app. It's minimal and fast, intended to be used as a browser bookmarklet on the currently-visible page.


Background
----------

First iteration of the shortgirls.net URL shortener. I used to use bit.ly a fair bit, but what annoyed me the most was that it was slow, and just made it tedious to get a bloody short URL!

shortgirls.net wouldn't necessarily make the Shortest URLs In The World, but it would be fast and work on my own terms.


Installation
------------

shortgirls.py is a single file, it's up to you to run it in a WSGI container of some sort.

* Apache `mod_wsgi`
* gunicorn
* uwsgi


Dependencies
------------

shortgirls.py relies only Python Paste, to provide prettier debugging output in the event of an error. This could easily be coded out.


License
-------

shortgirls.py is licensed under the FreeBSD license ("2-clause BSD license").


Copyright
---------

shortgirls.py was written by Barney Desmond.


Contact
-------

Feedback and contributions are welcomed:

* barneydesmond@gmail.com
* [@furinkan](https://twitter.com/furinkan/)

If you make improvements to shortgirls.py it'd be nice if you shared them around equally.
