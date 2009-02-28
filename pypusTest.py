#!/usr/bin/env python
# -*- encoding: latin1 -*-

from unittest import TestCase, TestSuite, makeSuite, TextTestRunner
import pypus
import pylab

class TestPypusParser(TestCase):
    """PypusParser TestCase"""
    def setUp(self):
        """docstring for setUp"""
        pass
    
    def test_parser(self):
        """testing PypusParser"""
        code = '@numpy.log($1, [1,2,3], (1, 2), b=(1,2), 10L, 1.2, 1e-1, "wi()lson", {"d": 1, "a": 2} , a=1)'
        # code = '@numpy.log @numpy.diff'
        parser = pypus.PypusParser()
        l = parser.parse(code)
        print l[0].args
        print l[0].kwargs


if __name__ == '__main__':
    suite = TestSuite()
    suite.addTest(makeSuite(TestPypusParser))
    runner = TextTestRunner(verbosity=2)
    runner.run(suite)
