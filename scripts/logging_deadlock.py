# test deadlock

import logging
import logging.config
import threading
import time
import os


def tick(msg):
    print(time.strftime("%H:%M:%S"), msg)

class CustomHandler(logging.Handler):
    def emit(self, record):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.isEnabledFor(logging.INFO)

def log_loop():
    while True:
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.info("some log")
        tick('hello from log_loop')

def config_loop():
    while True:
        config_once()

def config_once():
    logging.config.dictConfig({
            'version': 1, 
            'handlers': {
                'custom': {'class': 'logging_deadlock.CustomHandler'}
            },
            'root': {
                'handlers': ['custom']
            }
        }
    )
    tick(f"hello from config_once. pid: {os.getpid()}") 


if __name__ == '__main__':
    t1 = threading.Thread(target=log_loop, name='log_loop')
    t1.start()

    t2 = threading.Thread(target=config_loop, name='config_loop')
    t2.start()

