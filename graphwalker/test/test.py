#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
import unittest


if __name__ == '__main__':
    import os
    import sys

    names = [name[:-3]
             for name in os.listdir(os.path.dirname(__file__))
             if name.endswith('_test.py')]

    for name in names:  # preload all test modules.
        __import__('graphwalker.test.' + name)

    unittest.main(module='graphwalker.test', argv=sys.argv + names)
