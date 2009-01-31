#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Provides from_cache and to_cache, for loading/storing data to hard disk.

from_cache returns local data related to id from cache dir.
to_cache stores into a local file in cache dir data related to id.

Test usage: python cachhe.py
"""

from __future__ import with_statement # Backward compatibility with Python 2.5
import os
import pickle
import unittest

__author__ = "Claudio Baccigalupo"

def get_cache_path(id, cache_dir, ext=None):
    '''Convert 123456789012 into [cache_dir]/123/456/789/012[ext].txt.'''
    path = "/".join([str(id).zfill(12)[3*i:3*i+3] for i in range(4)])
    if ext is not None:
        path = path + ext
    return os.path.join(cache_dir, path + ".txt")

def from_cache(id, cache_dir, ext=None):
    '''Return data of id from cache, False if error.'''
    try:
        path = get_cache_path(id, cache_dir, ext)
        with open(path, 'r') as f:
            return pickle.load(f)
    except (IOError, TypeError, AttributeError):
        return False

def to_cache(id, cache_dir, data, ext=None):
    '''Store data into local file, False if error.'''
    try:
        path = get_cache_path(id, cache_dir, ext)
        folder = os.path.split(path)[0]
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(path, 'w') as f:
            pickle.dump(data, f)
        return True
    except (IOError, TypeError, OSError, AttributeError):
        return False
 
class TestCache(unittest.TestCase):
    
    def setUp(self):
        self.id = 999999999999
        self.cache_dir = "cache"
        self.path = get_cache_path(self.id, self.cache_dir)
    
    def tearDown(self):
        if os.path.exists(self.path): 
            os.remove(self.path) 
        
    def testCache(self):
        to_cache(self.id, self.cache_dir, "Test")
        self.assertEqual("Test", from_cache(self.id, self.cache_dir))

if __name__ == '__main__':
    unittest.main()
                