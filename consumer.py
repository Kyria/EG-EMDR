import zlib
import random

import MySQLdb
import gevent
import simplejson
import zmq.green as zmq

from dateutil import parser
from datetime import datetime
from gevent import monkey;
from gevent.pool import Pool
from itertools import groupby


from config import settings

# gevent monkey patch
gevent.monkey.patch_all()

class emdr_consumer:

    history_query = "INSERT IGNORE INTO emdr_price_history (type_id, `date`, orders, quantity, low, high, average, region_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    order_query = "INSERT IGNORE INTO emdr_raw_price (type_id, generated_at, orders, sell_price, buy_price, vol_remaining, vol_entered, region_id, solar_system_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    
    def main(self):
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

        print("Consumer daemon started, waiting for jobs...")
        print("Worker pool size: %d" % greenlet_pool.size)
        
        while True:
            # let's start working
            greenlet_pool.spawn(self.worker, subscriber.recv())
            
    def init_data(self,columns, row, generated_at, type_id, region_id):
        data = dict(zip(columns, row))
        data['generatedAt'] = generated_at
        data['typeID'] = type_id
        data['regionID'] = region_id
        return data

    def worker(self,compressed_json):
        """
        For every incoming message, this worker function is called. Be extremely
        careful not to do anything CPU-intensive here, or you will see blocking.
        Sockets are async under gevent, so those are fair game.
        """
        
        start_time = datetime.now()

        # uncompress
        market_data = simplejson.loads(zlib.decompress(compressed_json))
        
        # start parsing
        columns = market_data['columns']
        data_type = market_data['resultType']
        
        db = MySQLdb.connect(settings.DB_HOST, settings.DB_USER, settings.DB_PASS, settings.DB_NAME)
        cursor = db.cursor()
        
        for rowset in market_data['rowsets']:
            
            generated_at = parser.parse(rowset['generatedAt']).strftime('%Y-%m-%d %H:%M:%S')
            type_id = int(rowset['typeID'])
            region_id = int(rowset['regionID'])
                    
            if data_type == 'history': 
                if region_id not in settings.REGIONS:
                    continue
                
                query_values_hist = []
                for row in rowset['rows']:
                    data = self.init_data(columns, row, generated_at, type_id, region_id)
                    
                    data['date'] = parser.parse(data['date']).date().isoformat()

                    # trying to insert and catch exception is the fastest way to manage duplicates.
                    #print : self.history_query % (type_id, data['date'], data['orders'], data['quantity'], data['low'], data['high'], data['average'], region_id)
                    query_values_hist.append((type_id, data['date'], data['orders'], data['quantity'], data['low'], data['high'], data['average'], region_id))
                    #print "Debug : KO (%d, %s, %d)" % (type_id, data['date'],region_id)

                if query_values_hist:
                    cursor.executemany(self.history_query,query_values_hist)
                    db.commit()

                
            elif data_type == 'orders':
                by_system = {}
                query_values_order = []

                for row in rowset['rows']:
                    order = self.init_data(columns, row, generated_at, type_id, region_id)
                
                    order['issueDate'] = parser.parse(order['issueDate'])
                    if order['solarSystemID'] in settings.SOLAR_SYSTEMS:
                        if order['solarSystemID'] not in by_system:
                            by_system[order['solarSystemID']] = []
                        by_system[order['solarSystemID']].append(order)
                    else:
                        continue

                for system, orders in by_system.iteritems():
                    #bid = attrgetter('bid')
                    sort = sorted(orders, key=lambda x: x["bid"])
                    
                    bids = {k:list(g) for k,g in groupby(sort, key=lambda x: x["bid"])}
                    max_bid = max(o['price'] for o in bids[True]) if True in bids else None
                    min_sell = min(o['price'] for o in bids[False]) if False in bids else None
                    vol_remaining = sum(o['volRemaining'] for o in bids[False]) if False in bids else None  
                    vol_entered = sum(o['volEntered'] for o in bids[False]) if False in bids else None  
                    orders_number = int(len(orders))
                    
                    #print self.order_query % (type_id, generated_at, orders_number, min_sell, max_bid, vol_remaining, vol_entered, region_id, system)
                    query_values_order.append((type_id, generated_at, orders_number, min_sell, max_bid, vol_remaining, vol_entered, region_id, system))
                
                if query_values_order:
                    cursor.executemany(self.order_query,query_values_order)
                    db.commit()
            
        time_diff = datetime.now() - start_time
        gen = market_data['generator']['name']
        print "Debug : worker time : %s - %d ms" % (data_type, time_diff.microseconds/100)
        
        
    # check generation date
    #   item.max_bid = max(o.price for o in bids[True]) if True in bids else None
    #                    item.min_sell = min(o.price for o in bids[False]) if False in bids else None
        
if __name__ == '__main__':
    consumer = emdr_consumer() 
    consumer.main()

    