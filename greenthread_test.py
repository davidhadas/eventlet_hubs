import sys
import eventlet
from eventlet.green import urllib2

from eventlet_hubs import selectHub, pollHub, epollHub

#eventlet.hubs.use_hub(selectHub)
#eventlet.hubs.use_hub(pollHub)
#eventlet.hubs.use_hub(epollHub)



def some_long_calculation():  # or anything else making the server cpu bound
    x = 0
    for i in xrange(1,1000000): # may need to be adjusted for your system
         x =  i + x / i 

def count_url(url):
    try:
        with eventlet.Timeout(3):
            body = urllib2.urlopen(url).read()  # takes less than 3 seconds
    except eventlet.Timeout:
        print 'timeout %s' % url # you would not expect to have timeouts - but you do
        return
    print '-->done %s' % url # you would not expect to have timeouts - but you do
    some_long_calculation()

urls = ['http://eventlet.net']*100
pile = eventlet.GreenPile()
for x in urls:
    eventlet.sleep(0.01)  # increasing this solves the problem
    pile.spawn(count_url, x)



