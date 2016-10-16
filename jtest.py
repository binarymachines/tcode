#!/usr/bin/env python


from journaling import journal, CouchbaseOpLog


      
oplog = CouchbaseOpLog(host='localhost', bucket='default')

@journal('dummy_op', oplog)
def do_something():
    print '### This is an operation.'


do_something()
