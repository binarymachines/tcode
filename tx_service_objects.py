#!/usr/bin/env python


import os
import core
import couchbase
import couchbasedbx as cdb
from couchbase.n1ql import N1QLQuery
from couchbase.views.iterator import View
from couchbase.views.params import Query

from pymongo import MongoClient
from pymongo.database import Database

import unirest
import requests
import json
from datetime import datetime

from dsxutil import *

class MerchantType():
    def __init__(self):
        pass

    @staticmethod
    def RESTAURANT():
        return 'R'

    @staticmethod
    def CATERER():
        return 'C'

    @staticmethod
    def FLORIST():
        return 'F'

    @staticmethod
    def GROGERY_STORE():
        return 'I'

    @staticmethod
    def WINE_LIQUOR():
        return 'W'

    @staticmethod
    def DRUGSTORE():
        return 'U'

    @staticmethod
    def PET_STORE():
        return 'P'

    @staticmethod
    def TOBACCO():
        return 'Z'


class OrderItem(object):
    def __init__(self, item_id, quantity, label="", instructions=""):
        self.item_id = item_id
        self.item_qty = quantity
        self.option_qty = {}
        self.item_label = label
        self.instructions = instructions


    def add_option(self, option_id, quantity):
        self.option_qty[option_id] = quantity
        return self

    
        
class OrderUpdateBuilder(object):
    def __init__(self, client_id, order_type, instructions):
        self.client_id = client_id
        self.order_type = order_type
        self.instructions = instructions
        self.items = []

    def add_item(self, order_item):
        self.items.append(order_item.__dict__)

    def build(self):
        return self.__dict__

    
    
class GeoCoordinates(object):
    def __init__(self, lat, long):
        self.lat = lat
        self.long = long


class CouchbaseRecord(object):
    def __init__(self, record_type):
        self.record_type = record_type


    def generate_key(self):
        pass

    
# TODO: change these to be RecordBuilders, so that we can build any new record object
# from initial parameters _or_ from a JSON object pulled from the DB
    
        
class MerchantRecord(CouchbaseRecord):
    def __init__(self, json_rec):
        CouchbaseRecord.__init__(self, 'restaurant')        
        setattr(self, 'id', json_rec['id'])
        setattr(self, 'name', json_rec['summary']['name'])
        setattr(self, 'tags', json_rec['summary']['cuisines'])
        setattr(self, 'location', json_rec['location'])
        setattr(self, 'ordering', json_rec['ordering'])
        setattr(self, 'timestamp', str(datetime.now()))        


        
class MenuListRecord(CouchbaseRecord):
    def __init__(self, menu_table, restaurant_id):
        CouchbaseRecord.__init__(self, 'menu_list')        
        setattr(self, 'restaurant_id', restaurant_id)
        setattr(self, 'menus', menu_table)
        setattr(self, 'timestamp', str(datetime.now()))


        

class MenuRecord(CouchbaseRecord):
    def __init__(self, json_rec, restaurant_id):
        CouchbaseRecord.__init__(self, 'menu')

        setattr(self, 'id', json_rec['id'])
        setattr(self, 'name', json_rec['name'])
        setattr(self, 'description', json_rec['description'])
        setattr(self, 'children', json_rec['children'])
        setattr(self, 'restaurant_id', restaurant_id)
        setattr(self, 'timestamp', str(datetime.now()))

        
class TokenRecord(CouchbaseRecord):
    def __init__(self, json_rec):
        CouchbaseRecord.__init__(self, 'guest_token')
        setattr(self, 'token', json_rec['Guest-Token'])
        setattr(self, 'is_valid', True)
        setattr(self, 'timestamp', str(datetime.now()))


        
class TeamRecord(CouchbaseRecord):
    def __init__(self, team_name, admin_id, guest_token):
        CouchbaseRecord.__init__(self, 'team')
        
        setattr(self, 'name', team_name)
        setattr(self, 'admin', admin_id)
        setattr(self, 'auth_token', guest_token)
        setattr(self, 'timestamp', str(datetime.now()))

        
class TeamMemberCartRecord(CouchbaseRecord):
    def __init__(self, team_name, user_id):
        CouchbaseRecord.__init__(self, 'team_member_cart')

        setattr(self, 'userid', user_id)
        setattr(self, 'timestamp', str(datetime.now()))


class ContextRecord(CouchbaseRecord):

    def __init__(self, address, fulfillment_type, available_food_types, team_id, team_admin_id):
        CouchbaseRecord.__init__(self, 'delivery_context')

        setattr(self, 'address', address)
        setattr(self, 'fulfillment_type', fulfillment_type)
        setattr(self, 'available_food_types', available_food_types)
        setattr(self, 'slack_team_id', team_id)
        setattr(self, 'slack_team_admin_id', team_admin_id)
        setattr(self, 'preferences', [])
        setattr(self, 'timestamp', str(datetime.now())) 
        
        
        
    
class CouchbaseServiceObject():
    def __init__(self, logger, **kwargs):
        couchbase_host = kwargs['hostname']
        self.bucket_name = kwargs['bucket_name']
        
        self.logger = logger
        self.logger.info('couchbase host is: %s' % couchbase_host)
        self.logger.info('couchbase bucket is: %s' % self.bucket_name)
        self.couchbase_db = cdb.CouchbaseServer(couchbase_host)
        self.cpmgr = cdb.CouchbasePersistenceManager(self.couchbase_db, self.bucket_name)
        self.bucket = self.couchbase_db.get_bucket(self.bucket_name)
        

    def merchant_key_from_id(self, merchant_record_id):
        return 'restaurant_%s' % merchant_record_id


    def menu_key_from_id(self, menu_id, merchant_record_id):
        return 'menu_%s_restaurant_%s' % (menu_id, merchant_record_id)


    def menulist_key_from_merchant_id(self, merchant_record_id):
        return 'menu_list_restaurant_%s' % merchant_record_id


    def team_key_from_name(self, team_name):
        return 'team_%s' % team_name

    
    def context_key_from_team_id(self, team_id):
        return 'delivery_context_%s' % team_id
        

    def save_cart_data(self, input_data, cart):
        self.logger.info('Saving delivery.com cart record:\n%s' % cart)
        self.logger.info('Client request from node layer was:\n%s' % input_data)
    
        
    def save_merchant_records(self, merchant_records):
        self.logger.info('### Saving merchant records to Couchbase bucket %s...' % self.bucket_name)

        for record in merchant_records:
            key = self.merchant_key_from_id(record.id)
            self.bucket.upsert(key, record.__dict__)

            
    def save_menu_records(self, menu_records, merchant_id):
        self.logger.info('### Saving menu records to Couchbase bucket %s...' % self.bucket_name)

        for record in menu_records:
            key = self.menu_key_from_id(record.id, merchant_id)
            self.bucket.upsert(key, record.__dict__)

            
    def save_menulist_record(self, menulist_record, merchant_id):
        key = self.menulist_key_from_merchant_id(merchant_id)
        self.bucket.upsert(key, menulist_record.__dict__)


        
    def lookup_required_option_groups(self, menuitem_id):        
        q = Query(stale=False,inclusive_end=True, mapkey_single=menuitem_id)
        resultset = []
        for result in View(self.bucket, 'dev_dsx', 'menu_item_required_options', query=q):
            resultset.append(result.value)
        return resultset


    def lookup_all_option_groups(self, menuitem_id):        
        q = Query(stale=False,inclusive_end=True, mapkey_single=menuitem_id)
        resultset = []
        for result in View(self.bucket, 'dev_dsx', 'menu_item_options', query=q):
            resultset.append(result.value)
        return resultset
    

    def lookup_menu(self, merchant_id, menu_id) :

        q = N1QLQuery('SELECT * FROM %s WHERE id=$id AND record_type=$record_type AND restaurant_id=$merchant_id' % self.bucket_name,
               id=menu_id, record_type='menu', merchant_id=merchant_id)

        self.logger.info('### Executing lookup query: %s ...' % str(q))

        menus = []
        resultset = self.bucket.n1ql_query(q)
        self.logger.info('### query returned resultset of type %s.' % resultset.__class__.__name__)
        for record in resultset:
            self.logger.info('### appending record to response.')
            menus.append(record)

        if len(menus):
            return menus[0]
        return []


    # TODO: get a uniform way of creating context records
    def save_delivery_context(self, raw_context_data): 

        self.logger.info('updating delivery context %s in database...' % raw_context_data)
        try:

            context_data = raw_context_data

            self.logger.info('### Here is the slack team context info: %s' % context_data)
            
            self.logger.info('### Here is the slack team ID: %s' % context_data["slack_team_id"])
            
            key = self.context_key_from_team_id(context_data.get('slack_team_id'))
            self.logger.info('context key is: %s' % key)
            
            self.bucket.replace(key, context_data)
            
            self.logger.info('delivery context updated.')
            return key
        except couchbase.exceptions.NotFoundError, err:
            raise Exception('Key not found in DB: %s. Error message: %s' % (key, err.message))
        
    

    def lookup_delivery_context(self, team_id, admin_id):
        self.logger.info('looking up delivery context for team %s and admin %s...' % (team_id, admin_id))
        q = N1QLQuery('SELECT * FROM %s WHERE record_type=$record_type AND slack_team_id=$team_id AND slack_team_admin_id=$team_admin_id' % self.bucket_name,
               record_type='delivery_context', team_id=team_id, team_admin_id=admin_id)

        resultset = self.bucket.n1ql_query(q)
        results = []
        for record in resultset:
             
            results.append(record['default'])

        if not results:
            raise Exception('No team context found for team ID %s and admin ID %s.' % (team_id, admin_id))
         
        if len(results) > 1:
            raise Exception('Duplicate team context found for team ID %s and admin ID %s.' % (team_id, admin_id))

        return results[0]
        

    
    def create_delivery_context(self, address, 
                                fulfillment_type,
                                available_food_types,
                                team_id,
                                team_admin_id):
        
        key = self.context_key_from_team_id(team_id)

        # TODO: CouchbaseRecordBuilder with two build methods:
        # init() and from_json()
        #        
        context_record = ContextRecord(address, fulfillment_type, available_food_types, team_id, team_admin_id)

        ## WARNING WARNING: we are overwriting the delivery context every time
        ## TODO: figure out a repeatable UUID/ key generation strategy
        self.bucket.upsert(key, context_record.__dict__) 
        return context_record
    
        
    
    def create_team(self, team_name, admin_id, guest_token):
        key = self.team_key_from_name(team_name)

        team_record = TeamRecord(team_name, admin_id, guest_token.token)
        self.bucket.insert(key, team_record.__dict__)
        return team_record


    
    def lookup_team(self, team_name):
        key = self.team_key_from_name(team_name)
         # TODO: update this logic when we start running on cluster
        result = self.bucket.get(key, quiet=True)
        if result.success:
            return result.value
        return None

    

class MongoDBClient():
    def __init__(self, logger, **kwargs):
        self.logger = logger        
        self.host_array = kwargs.get('hosts')
        self.replicaset = kwargs.get('replicaset')
        self.db_name = kwargs.get('database_name')
        
        if not self.replicaset:
            host_tokens = self.host_array[0].split(':')
            
            hostname = host_tokens[0]
            port = 27017
            if len(host_tokens) == 2:
                port = int(host_tokens[1])
            
            mdb_client = MongoClient(host=hostname, port=port)
            self.db = Database(mdb_client, self.db_name)
        else:
            raise Exception('Connect-to-replicaset not yet implemented (but coming soon)')


        
class DeliveryAPIClient():
    def __init__(self, logger, **kwargs):
        self.logger = logger
        self.client_id = kwargs.get('client_id')
        self.base_url = 'https://api.delivery.com'
        self.merchant_search_endpoint = 'merchant/search/delivery'

        
    def create_new_guest_token(self):
        url = '/'.join([self.base_url, '/customer/auth/guest'])
        params = {}
        params['client_id'] = self.client_id

        response = unirest.get(url, params=params)
        if response.code == 200:
            return TokenRecord(response.body)
        raise DeliveryAPIException(url, response.code, response.body)
        

    def get_team_cart(self, guest_token, restaurant_id):
        url = '/'.join([self.base_url, 'customer/cart/%s' % restaurant_id])
        headers = {}
        headers['Guest-Token'] = guest_token
        params = {}
        params['order_type'] = 'delivery'
        params['client_id'] = self.client_id

        self.logger.info('Issuing delivery API call to endpoint: %s' % url)
        self.logger.info('parameters: %s' % params)
        self.logger.info('request headers: %s' % headers)

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        raise DeliveryAPIException(url, response.status_code, response.json())


    def update_team_cart(self, item_data):

        self.logger.info(item_data)
        
        restaurant_id = item_data.pop('restaurant_id')
        
        url = '/'.join([self.base_url, 'customer/cart/%s' % restaurant_id])
        headers = {}
        headers['Content-Type'] = 'application/json'  
        headers['Guest-Token'] = item_data.pop('guest_token')      

        params = item_data
        params['order_type'] = 'delivery'
        params['client_id'] = self.client_id
        params['order_time'] = 'ASAP'

        self.logger.info('Generated URL: %s' % url)
        self.logger.info('Passing headers: %s' % headers)
        self.logger.info('Passing request body: %s' % params)

        
        response = requests.post(url, headers=headers, data=json.dumps(params))
        if response.status_code == 200:
            return response.json()
        raise DeliveryAPIException(url, response.status_code, response.json())


    def remove_from_team_cart(self, guest_token, restaurant_id, item_index):        
        params = {'client_id': self.client_id}
        params['cart_index'] = item_index
        
        headers = {}
        headers['Guest-Token'] = guest_token
        headers['Content-Type'] = 'application/json'

        url = '/'.join([self.base_url, 'customer/cart/%s' % restaurant_id])
        response = requests.delete(url, headers=headers, data=json.dumps(params))

    
    def clear_team_cart(self, guest_token, restaurant_id):
        params = {'client_id': self.client_id }
        headers = {}
        headers['Guest-Token'] = guest_token
        headers['Content-Type'] = 'application/json'

        url = '/'.join(self.base_url, 'customer/cart/%s' % restaurant_id)
        response = requests.delete(url)
        if response.status_code == 200:
            return response.json()
        raise DeliveryAPIException(url, response.status_code, response.json())
        
    
        
    def generate_menulist_from_records(self, menu_records, restaurant_id):
        menu_table = {}
        for record in menu_records:
            menu_table[record.name] = record.id

        return MenuListRecord(menu_table, restaurant_id)
            
        

    def menu_search(self, restaurant_id):
        url = '/'.join([self.base_url, 'merchant/%d/menu' % int(restaurant_id)])
        params = {}
        params['client_id'] = self.client_id
        params['merchant_id'] = restaurant_id
        params['hide_unavailable'] = 1
        params['item_only'] = 1

        self.logger.info('### Menu search URL: %s' % url)
        self.logger.info('request parameters: %s' % params)
        
        response = unirest.get(url, params=params)
        if response.code == 200:
            menus = []
            menu_names = []
            
            for entry in response.body['menu']:     
                for c in entry['children']:                                             
                    menus.append(MenuRecord(c, restaurant_id) )
                                    
            return menus
        raise DeliveryAPIException(url, response.code, response.body)



    def get_food_types_near_address(self, address):
        url = '/'.join([self.base_url, self.merchant_search_endpoint])
        params = {}
        params['client_id'] = self.client_id
        params['address'] = address
        params['merchant_type'] = MerchantType.RESTAURANT()

        response = requests.get(url, params=params)
        if response.status_code == 200:
            self.logger.info(response.json()['cuisines'])
            return response.json()['cuisines']
        raise DeliveryAPIException(url, response.status_code, response)
        
    
        
    def restaurant_search(self, address, geo_coords=None):
        url = '/'.join([self.base_url, self.merchant_search_endpoint])
        params = {}
        params['client_id'] = self.client_id
        params['address'] = address
        params['merchant_type'] = MerchantType.RESTAURANT()

        self.logger.info('request parameters: %s' % params)
        
        response = unirest.get(url, params=params)

        if response.code == 200:
            merchants = []
            for entry in response.body['merchants']:                
                self.logger.info(entry.__class__.__name__)
                merchants.append(MerchantRecord(entry))

            self.logger.info(merchants[0].__dict__)
            return merchants
        
        raise DeliveryAPIException(url, response.code, response.body)
            



 
