#!/usr/bin/env python


from journaling import journaling



@journaling('foobar')
def do_something():
    print '### This is an operation.'


do_something()
