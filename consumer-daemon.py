#!/usr/bin/python
import emdr_consumer

import logging
import time

#third party libs
from daemon import runner

from config import settings

class ConsumerDaemon():
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path =  settings.DAEMON_PID_FILE_PATH
        self.pidfile_timeout = 5
        
        # init the consumer
        self.consumer = emdr_consumer.EMDRConsumer()    
        
    def run(self):      
        print "START"
        self.consumer.run()
        print "STOP!"

        
        
if __name__ == '__main__':
    consumer_daemon = ConsumerDaemon()

    logger = logging.getLogger(settings.LOGGER_NAME)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(settings.LOGGER_FORMATTER, settings.LOGGER_DATE_FORMAT)
    handler = logging.FileHandler(settings.LOGGER_LOG_FILE)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
        
    daemon_runner = runner.DaemonRunner(consumer_daemon)
    daemon_runner.daemon_context.files_preserve=[handler.stream]
    daemon_runner.do_action()
