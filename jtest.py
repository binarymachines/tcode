#!/usr/bin/env python


from journaling import journal


      
oplog = CouchbaseOpLog(host='localhost', bucket='default')

@journal(oplog)
def do_something():
    print '### This is an operation.'


do_something()
