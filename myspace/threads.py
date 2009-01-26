#!/usr/bin/env python

# 2009 - Claudio Baccigalupo

import threading
from Queue import Queue
import logging
import unittest

# ###########################
# Thread-related functions
# ###########################

class FunctionThreader(threading.Thread):
    def __init__(self, function, data, params):
        threading.Thread.__init__(self) # init from parent
        self.function = function
        self.data = data
        self.params = params
        self.result = None
 
    def get_result(self):
        return self.result
 
    def run(self):
        self.result = self.function(self.data, **self.params)

def call_threaded(function, data, queueSize=10, params={}):
    def producer_get(q, function, data):
        for item in data:
            thread = FunctionThreader(function, item, params)
            thread.start()
            q.put(thread, True)

    finished = []
    def consumer(q, count_threads):
        missing = count_threads - len(finished)
        while missing > 0:
            thread = q.get(True)
            thread.join()
            finished.append(thread.get_result())
            if missing % 50 == 0:
                logging.info("[%d more to load]" % missing)
            missing = count_threads - len(finished)

    q = Queue(queueSize)
    prod_thr = threading.Thread(target=producer_get, args=(q, function, data))
    cons_thr = threading.Thread(target=consumer, args=(q, len(data)))
    prod_thr.start()
    cons_thr.start()
    prod_thr.join()
    cons_thr.join()
    return finished
    
    
class TestCache(unittest.TestCase):

    def testThreads(self):
        oct_50 = [oct(i) for i in range(50)]
        self.assertEqual(oct_50, call_threaded(oct, range(50), 10))
        # Add more tests if needed

if __name__ == '__main__':
    unittest.main()
