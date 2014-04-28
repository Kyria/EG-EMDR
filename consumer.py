import zlib
import random

import MySQLdb
import simplejson
import gevent
from gevent.pool import Pool
from gevent import monkey;
import zmq.green as zmq

from config import settings

# gevent monkey patch
gevent.monkey.patch_all()


def main():
    """
    The main flow of the application.
    """
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    
    # remove filters
    subscriber.setsockopt(zmq.SUBSCRIBE, "")

    # connect to one of the relay
    relay = random.choice(settings.RELAYS)
    subscriber.connect(relay)
    print("Relay chosen : %s" % relay)

    # We use a greenlet pool to cap the number of workers at a reasonable level.
    greenlet_pool = Pool(size=settings.MAX_NUM_POOL_WORKERS)

    db = MySQLdb.connect(settings.DB_HOST, settings.DB_USER, settings.DB_PASS, settings.DB_NAME)
    print("Consumer daemon started, waiting for jobs...")
    print("Worker pool size: %d" % greenlet_pool.size)

    while True:
        try:
            # let's start working
            greenlet_pool.spawn(worker, subscriber.recv(), db)
        

        except KeyboardInterrupt:
            db.close()
            break
            
def init_data(columns, row, generated_at, type_id, region_id):
    data = dict(zip(columns, row))
    data['generatedAt'] = generated_at
    data['typeID'] = type_id
    data['regionID'] = region_id
    return data

def worker(compressed_json, db):
    """
    For every incoming message, this worker function is called. Be extremely
    careful not to do anything CPU-intensive here, or you will see blocking.
    Sockets are async under gevent, so those are fair game.
    """
    
    # need to benchmark this
    cursor = db.cursor()
    # and this
    # db = MySQLdb.connect(settings.db_host, settings.db_user, settings.db_pass, settings.db_name)
    # cursor = db.cursor()
    # --> not forget db.close !
    
    #lines = cursor.execute(query)


    market_data = simplejson.loads(zlib.decompress(compressed_json))
    
    if type == 'history':
        
    elif type == 'order':
    # Save to your choice of DB here.
    print market_data

# check generation date
#   item.max_bid = max(o.price for o in bids[True]) if True in bids else None
#                    item.min_sell = min(o.price for o in bids[False]) if False in bids else None
    
if __name__ == '__main__':
    main()

    