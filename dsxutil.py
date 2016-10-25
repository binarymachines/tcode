#!/usr/bin/env python



class DeliveryAPIException(Exception):
    def __init__(self, url, http_response, code = None):
        Exception.__init__(self, 'Error: the Delivery.com API responded to URL %s with status %s' % (url, http_response))
        self.data = code
