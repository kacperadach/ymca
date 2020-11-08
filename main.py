#!/usr/bin/python
from ymca import *
from time import sleep

def run():
    while 1:
        try:
            book(FITNESS_URL, FREE_WEIGHTS_NAME, KACPER)
            # book(POOL_URL, LAP_SWIM_NAME, ALEX)
            sleep(10 * 60)
        except Exception as e:
            logger.exception('Error: {}'.format(e))

if __name__ == '__main__':
    run()
