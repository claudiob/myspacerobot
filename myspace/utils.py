#!/usr/bin/env python
"""Provides auxiliary functions.

"""

import operator

__author__ = "Claudio Baccigalupo"

# ###########################
# Auxiliary functions
# ###########################

def intersect(a, b):
    '''Return the intersection of two lists.'''
    return list(set(a) & set(b))

def difference(a, b):
    '''Return the difference of two lists.'''
    return list(set(a) - set(b))

def is_digit(char): 
    '''Return true if char is a digit.'''
    return ord(char) in range(ord('0'),ord('9')+1)

def flatten(l):
    l = filter(None, l)
    # TEST THIS: return reduce(operator.add, l) if len(l) > 0 else l
    if len(l) > 0:
        l = reduce(operator.add, l)
    return l

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def read_int(arg):
    try:
        return int(arg)
    except (TypeError, ValueError):
        raise Usage("The specified value is not an integer")

