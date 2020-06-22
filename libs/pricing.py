import falcon
import json 
from datetime import datetime
from datetime import timezone
import mongodb

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from falcon_apispec import FalconPlugin
from marshmallow import Schema, fields

import calendar 


class MAPricingResource:
    def __init__(self):
        self.mydb=mongodb.Mongodb()
    def on_get(self, req, resp):
        dt_object = datetime.now()
        if 'timestamp' in req.params:
          try:
              dt_object = datetime.utcfromtimestamp(int(req.params['timestamp']))
          except TypeError as e:
              #Timestamp not valid, revert to now()
              print (e)
              dt_object = datetime.now()
          except Exception:
              resp.status=falcon.HTTP_401
              return 
        
        block=self.mydb.find_last("blocks",{'header.timestamp':{'$lte':dt_object}})
        response={}
        response['prices']=block['header']['pricing_record']
        response['timestamp']=timestamp
        response['block_timestamp']=block['header']['timestamp']
        
        resp.body = json.dumps(response)
        resp.status=falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON

class SpotPricingResource:
    def __init__(self):
        self.mydb=mongodb.Mongodb()

    def on_get(self, req, resp):
        dt_object = datetime.now()
        if 'timestamp' in req.params:
          try:
              dt_object = datetime.utcfromtimestamp(int(req.params['timestamp']))
          except TypeError as e:
              #Timestamp not valid, revert to now()
              print (e)
              dt_object = datetime.now()
          except Exception:
              resp.status=falcon.HTTP_401
              return 
        
   
        block=self.mydb.find_last("blocks",{'header.timestamp':{'$lte':dt_object}})
        response={}
        response['prices']=block['pricing_spot_record']
        response['timestamp']=timestamp
        response['block_timestamp']=block['header']['timestamp']
        
        resp.body = json.dumps(response)
        resp.status=falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON