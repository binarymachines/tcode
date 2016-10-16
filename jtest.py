#!/usr/bin/env python


from journaling import journal, CouchbaseOpLog


      
oplog = CouchbaseOpLog(hostname='localhost', bucket='default')

@journal('decorator_test_op', oplog)
def test_decorator_mode():
    print '### This is a journaled operation.'


def test_context_manager_mode():
    with journal('context_mgr_test_op', oplog) as j:
        print '### This is also a journaled operation.'


        
def main():
    test_decorator_mode()
    test_context_manager_mode()


if __name__ == '__main__':
    main()
