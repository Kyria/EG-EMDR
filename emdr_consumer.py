# gevent monkey patch
import gevent
from gevent import monkey;
gevent.monkey.patch_all()

import logging
import random
import threading
import zlib

import MySQLdb
import gevent
import simplejson
import zmq.green as zmq

from dateutil import parser
from datetime import datetime
from gevent.pool import Pool
from itertools import groupby

from config import settings


logger = logging.getLogger(settings.LOGGER_NAME)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(settings.LOGGER_FORMATTER, settings.LOGGER_DATE_FORMAT)
handler = logging.FileHandler(settings.LOGGER_LOG_FILE)
handler.setFormatter(formatter)
logger.addHandler(handler)

class EMDRConsumer:

    history_query = "INSERT IGNORE INTO emdr_price_history (type_id, `date`, orders, quantity, low, high, average, region_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    order_query = "INSERT INTO emdr_daily_price (type_id, generated_at, orders, sell_price, buy_price, vol_remaining, vol_entered, region_id, solar_system_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    order_query_update = "UPDATE emdr_daily_price SET generated_at = %s, orders = %s, sell_price = %s, buy_price = %s, vol_remaining = %s, vol_entered = %s WHERE solar_system_id = %s AND type_id = %s"
    DUPLICATE_ENTRY_ERROR_CODE = 1062
    
    def run(self):
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
        logger.info("Relay chosen : %s" % relay)

        # We use a greenlet pool to cap the number of workers at a reasonable level.
        greenlet_pool = Pool(size=settings.MAX_NUM_POOL_WORKERS)

        logger.info("Consumer daemon started, waiting for jobs...")
        logger.info("Worker pool size: %d" % greenlet_pool.size)
        
        # starting purge
        if settings.AUTO_PURGE:
            logger.info("Purge is activated and will run once per day")
            self.purge_data()
        
        while True:
           #let's start working
           greenlet_pool.spawn(self.worker, subscriber.recv())
      
    def insert_daily_value(self, rowset, columns, generated_at, type_id, region_id, db):
        """
        Insert daily raw data only the latest
        """
        by_system = {}
        
        cursor = db.cursor()

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
            sort = sorted(orders, key=lambda x: x["bid"])
            
            bids = {k:list(g) for k,g in groupby(sort, key=lambda x: x["bid"])}
            max_bid = max(o['price'] for o in bids[True]) if True in bids else None
            min_sell = min(o['price'] for o in bids[False]) if False in bids else None
            vol_remaining = sum(o['volRemaining'] for o in bids[False]) if False in bids else None  
            vol_entered = sum(o['volEntered'] for o in bids[False]) if False in bids else None  
            orders_number = int(len(orders))
            
            try:
                cursor.execute(self.order_query,(type_id, generated_at, orders_number, min_sell, max_bid, vol_remaining, vol_entered, region_id, system))
                db.commit()
            except MySQLdb.Error as err:
                db.rollback()
                error_code = err[0]
                if error_code == self.DUPLICATE_ENTRY_ERROR_CODE:
                    cursor.execute(self.order_query_update,(generated_at, orders_number, min_sell, max_bid, vol_remaining, vol_entered, system, type_id))
                    db.commit()
                else:
                    message = err[1]
                    logger.error("MySQL Error : %s - %s" % (error_code, message))

    def insert_history(self, rowset, columns, generated_at, type_id, region_id, db):
        """
        Insert history per items
        """
        if region_id not in settings.REGIONS:
            return
        
        query_values_hist = []
        for row in rowset['rows']:
            data = self.init_data(columns, row, generated_at, type_id, region_id)
            data['date'] = parser.parse(data['date']).date().isoformat()

            query_values_hist.append((type_id, data['date'], data['orders'], data['quantity'], data['low'], data['high'], data['average'], region_id))

        if query_values_hist:
            cursor = db.cursor()
            cursor.executemany(self.history_query,query_values_hist)
            db.commit()
   
    def init_data(self,columns, row, generated_at, type_id, region_id):
        """
            helper 
        """
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
        
        # init database connection
        db = MySQLdb.connect(settings.DB_HOST, settings.DB_USER, settings.DB_PASS, settings.DB_NAME)
        
        # let's start
        for rowset in market_data['rowsets']:
            
            generated_at = parser.parse(rowset['generatedAt']).strftime('%Y-%m-%d %H:%M:%S')
            type_id = int(rowset['typeID'])
            region_id = int(rowset['regionID'])
            
            # message is for history
            if data_type == 'history' and settings.INSERT_HISTORY: 
                self.insert_history(rowset, columns, generated_at, type_id, region_id, db)
            # the current message is for orders   
            elif data_type == 'orders' and settings.INSERT_DAILY:
                self.insert_daily_value(rowset, columns, generated_at, type_id, region_id, db)
    
    def purge_data(self):
        """
        Purge all useless data
        """
        
        # ask the function to repeat itself every day (in case we don't restart the script)
        # not matter if this is done in this script or not, it will lock the tables and prevent 
        # the data to be consumed... 
        threading.Timer(86400, self.purge_data).start()
        
        # little echo for log
        logger.info("Purging useless data...")
             
        # init db 
        db = MySQLdb.connect(settings.DB_HOST, settings.DB_USER, settings.DB_PASS, settings.DB_NAME)
        cursor = db.cursor()

        logger.info("... purging price history older than %d days..." % (settings.HISTORY_DAYS_RETENTION,))
        # delete all history older than 365 day
        cursor.execute("DELETE FROM emdr_price_history where `date` < (UTC_TIMESTAMP() - INTERVAL %d DAY)" % settings.HISTORY_DAYS_RETENTION)
             
        # commit :)
        db.commit()
        
        logger.info("... Purging done")
    
    
   
if __name__ == '__main__':    
    consumer = EMDRConsumer() 
    consumer.run()

    