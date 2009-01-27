#!/usr/bin/env python

# 2009 - Claudio Baccigalupo
from __future__ import with_statement

import os
import pickle
import unittest

def to_cache(path, data):
    '''Store data into local file.'''
    folder = os.path.split(path)[0]
    if not os.path.exists(folder):
        try:
            os.makedirs(folder)
        except:
            return False
    with open(path, 'w') as f:
        pickle.dump(data, f)

def from_cache(path):
    '''Retrieve data from local file, False if file does not exist/error.'''
    try:
        with open(path, 'r') as f:
            return pickle.load(f)
    except IOError:
        return False
        
class TestCache(unittest.TestCase):
    
    def setUp(self):
        self.path = "cache/test.txt"
    
    def tearDown(self):
        if os.path.exists(self.path): 
            os.remove(self.path) 
        
    def testCache(self):
        to_cache(self.path, 1)
        self.assertEqual(1, from_cache(self.path))

if __name__ == '__main__':
    unittest.main()
                