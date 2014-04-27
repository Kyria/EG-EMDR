import zlib
import random

import simplejson
import gevent
from gevent.pool import Pool
import zmq.green as zmq

# gevent monkey patch
gevent.monkey.patch_all()

# The maximum number of greenlet workers in the greenlet pool. 
# This is not one # per processor, a decent machine 
# can support hundreds or thousands of greenlets.
# I recommend setting this to almost the maximum number of connections your database
# backend can accept, if you must open one connection per save op.
MAX_NUM_POOL_WORKERS = 200

# uncomment relay you want to use
relays = [
    #"tcp://relay-us-west-1.eve-emdr.com:8050"    , # Cogent    Sacramento, CA	
    #"tcp://relay-us-central-1.eve-emdr.com:8050" , # Ubuquity  Hosting	Chicago.
    #"tcp://relay-us-east-1.eve-emdr.com:8050"    , # Digital   Ocean	New York, NY
    #"tcp://relay-ca-east-1.eve-emdr.com:8050"    , # OVH US    Montreal, CA
    "tcp://relay-eu-germany-1.eve-emdr.com:8050" , # Hetzner   Germany
    "tcp://relay-eu-denmark-1.eve-emdr.com:8050" , # ComX      Denmark
]

def main():
    """
    The main flow of the application.
    """
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    
    # remove filters
    subscriber.setsockopt(zmq.SUBSCRIBE, "")

    # connect to one of the relay
    subscriber.connect(random.choice(relays)

    # We use a greenlet pool to cap the number of workers at a reasonable level.
    greenlet_pool = Pool(size=MAX_NUM_POOL_WORKERS)

    print("Consumer daemon started, waiting for jobs...")
    print("Worker pool size: %d" % greenlet_pool.size)

    while True:
        # let's start working
        greenlet_pool.spawn(worker, subscriber.recv())

def worker(compressed_json):
    """
    For every incoming message, this worker function is called. Be extremely
    careful not to do anything CPU-intensive here, or you will see blocking.
    Sockets are async under gevent, so those are fair game.
    """
    # Receive raw market JSON strings.
    market_json = zlib.decompress(compressed_json)
    # Un-serialize the JSON data to a Python dict.
    market_data = simplejson.loads(market_json)
    # Save to your choice of DB here.
    print market_data

if __name__ == '__main__':
    main()
