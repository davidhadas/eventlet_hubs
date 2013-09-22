eventlet_hubs
=============

Patch to eventlet hubs (See https://github.com/eventlet/eventlet/issues/50)

The patch loops on the select/poll/epoll until there is no more data and only 
than returns from Hub.wait() ensuring that timeout does not occur when it
should not.


Without this patch the following code:

    with Timeout(3):
        urllib2.urlopen(url).read()

may result in Timeout even long after the url has been retrieved
i.e. the url may be retrieved in well under 1 seconds and still the timeout would fire.

This is demonstrated by the attached code.

