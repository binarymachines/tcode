#!/usr/bin/env python


from functools import wraps


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



class JournalingService(object):
    def __init__(self, **kwargs):
        pass


    
    
class journal(ContextDecorator):
    def __init__(self, record_data):
        self.record_data = record_data


    def __enter__(self):
        print 'writing oplog START record: %s...' % self.record_data
        return self


    def __exit__(self, typ, val, traceback):
        print 'writing oplog END record: %s...' % self.record_data
        return self

    
