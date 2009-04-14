#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Provides call_threaded, for launching a function on multiple threads.

call_threaded takes a function and a series of data and launch the function
on a separate thread for each data item, then return the cumulative result.

Test usage: python threads.py
"""

from Queue import Queue
import threading
import logging
import unittest

__author__ = "Claudio Baccigalupo"

class FunctionThreader(threading.Thread):
    '''A threading class to invoke a function with given data and params.'''
    def __init__(self, function, data, params):
        threading.Thread.__init__(self)
        self.function = function
        self.data = data
        self.params = params
        self.result = None
 
    def get_result(self):
        return self.result
 
    def run(self):
        self.result = self.function(self.data, **self.params)

def call_threaded(function, data, queueSize=10, params={}):
    '''Create a queue of queueSize function threads and wait for completion.'''
    def producer(q, function, data):
        '''Create one thread for each item to evaluate.'''
        for item in data:
            thread = FunctionThreader(function, item, params)
            thread.start()
            q.put(thread, True)

    finished = []
    def consumer(q, count_threads):
        '''Wait for all the threads to complete.'''
        missing = count_threads - len(finished)
        while missing > 0:
            thread = q.get(True)
            thread.join()
            finished.append(thread.get_result())
            if missing % 25 == 0:
                logging.info("[%d more to load]" % missing)
            missing = count_threads - len(finished)

    q = Queue(queueSize)
    prod_thr = threading.Thread(target=producer, args=(q, function, data))
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
