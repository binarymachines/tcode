#!/usr/bin/env python


from functools import wraps
import os
import datetime




class OpLog(object):
    def __init__(self, **kwargs):
        pass


    def log_start(self, **kwargs):
        pass


    def log_end(self, **kwargs):
        pass
    

class CouchbaseOpLog(OpLog):
    def __init__(self, **kwargs):
        self.couchbase_server = CouchbaseServer('localhost')
        self.pmgr = CouchbasePersistenceManager(couchbase_server, 'default')


    def log_start(self, **kwargs):
        op_record = CouchbaseRecordBuilder('op_record').add_fields(kwargs).build()
        self.pmgr.insert_record(op_record)


    def log_end(self, **kwargs):
        op_record = CouchbaseRecordBuilder('op_record').add_fields(kwargs).build()
        self.pmgr.insert_record(op_record)
    


class ContextDecorator(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


    def __enter__(self):
        return self


    def __exit__(self, typ, val, traceback):
        pass


    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return wrapper

    
    
class journal(ContextDecorator):
    def __init__(self, op_name, op_log):
        self.op_log = op_log
        self.op_name = op_name


    def __enter__(self):
        print 'writing oplog START record...'
        record = dict(timestamp=datetime.datetime.now(),
                      phase='start',
                      pid=os.getpid(),
                      op_name=self.op_name)
        
        self.op_log.log_start(**record)
        return self


    def __exit__(self, typ, val, traceback):
        print 'writing oplog END record:...'
        record = dict(timestamp=datetime.datetime.now(),
                      phase='end',
                      pid=os.getpid())
        
        self.op_log.log_end(**record)
        return self

    
