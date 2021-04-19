import falcon
from falcon_caching import Cache
cache = Cache(config={'CACHE_TYPE': 'simple'})

import json 
from bson import json_util
import libs.utils
import coingecko

import blockchain
import mongodb
from datetime import datetime
from datetime import timezone
from dateutil.relativedelta import relativedelta

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from falcon_apispec import FalconPlugin
from marshmallow import Schema, fields
import calendar 

class InfoResource:
    def __init__(self):
        self.bc=blockchain.Blockchain()
        self.mongo=mongodb.Mongodb()
        self.tools=libs.utils.tools()
        self.cg=coingecko.Coingecko()
        self.currencies=self.mongo.find("currencies")

    #@cache.cached(timeout=10)
    def on_get(self, req, resp):
        dt_to = datetime.now()
        if 'timestamp' in req.params:
          try:
              dt_to = datetime.utcfromtimestamp(int(req.params['timestamp']))
          except TypeError as e:
              #Timestamp not valid, revert to now()
              print (e)
        query={'header.timestamp':{'$lte':dt_to}}
        LastBlock=self.mongo.find_last('blocks',query)
        dt_24= dt_to - relativedelta(days=1)
        query={'header.timestamp':{'$lte':dt_24}}
        LastBlock24=self.mongo.find_last('blocks',query)

        payload={}

        coingecko=json.loads(self.cg.getInfo("haven"))
        bc=self.bc.getInfo()['text']
        print (coingecko)
        print (bc)
        if 'currency' in req.params:
            self.currencies=self.mongo.find("currencies",{'xassetcase':req.params['currency'].upper()})

        self.currencies.rewind()
        # payload['db_lastblock']['height']=LastBlock['_id']
        # if LastBlock24 is not None:
        #     payload['db_lastblock24']['height']=LastBlock24['_id']
        for currency in self.currencies:
            asset={}
            asset['ticker']=currency['xasset']
            asset['name']=currency['name']
            
            if currency['xasset']=="XHV":
                asset['ma']=self.tools.convertFromMoneroFormat(LastBlock['header']['pricing_record']['unused1'])
                asset['spot']=self.tools.convertFromMoneroFormat(LastBlock['pricing_spot_record']['xUSD'])
            elif currency['xasset']=="xUSD":
                asset['spot']=1
                asset['ma']=1
            else:
                asset['ma']=1/self.tools.convertFromMoneroFormat(LastBlock['header']['pricing_record'][currency['xasset']]) if LastBlock['header']['pricing_record'][currency['xasset']]!=0 else 0
                asset['spot']=1/self.tools.convertFromMoneroFormat(LastBlock['pricing_spot_record'][currency['xasset']]) if LastBlock['pricing_spot_record'][currency['xasset']]!=0 else 0
            
            asset['supply']=LastBlock['cumulative']['supply_offshore'][currency['xasset']]
            asset['marketcap']=asset['supply']*asset['spot']
            payload[currency['xasset']]=asset


        resp.body =json.dumps(payload, ensure_ascii=False,default=json_util.default)
        resp.status=falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON

