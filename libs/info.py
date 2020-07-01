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
    
    @cache.cached(timeout=10)
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
        
        print (LastBlock)
        print (LastBlock24)
        payload={
            'coingecko':{},
            'bc':{},
            'db_lastblock':
            {
                'pricing_spot_record':{},
                'pricing_record':{},
                'spot_ma_deviation':{},
                'supply':{},
            },
            'db_lastblock24':
            {
                'pricing_spot_record':{},
                'pricing_record':{},
                'spot_ma_deviation':{},
                'supply':{},
            }
        }
        coingecko=json.loads(self.cg.getInfo("haven").text)
        del coingecko['description']
        payload['coingecko']=coingecko

        payload['bc']=self.bc.getInfo()['text']
        for currency in LastBlock['pricing_spot_record']:
            #Pricing spot record
            payload['db_lastblock']['pricing_spot_record'][currency]=self.tools.convertFromMoneroFormat(LastBlock['pricing_spot_record'][currency])
            payload['db_lastblock24']['pricing_spot_record'][currency]=self.tools.convertFromMoneroFormat(LastBlock24['pricing_spot_record'][currency])
            #pricing record
            if 'pricing_record' in LastBlock24['header'] and currency in LastBlock24['header']['pricing_record']:
                payload['db_lastblock']['pricing_record'][currency]=self.tools.convertFromMoneroFormat(LastBlock['header']['pricing_record'][currency])
                payload['db_lastblock24']['pricing_record'][currency]=self.tools.convertFromMoneroFormat(LastBlock24['header']['pricing_record'][currency])
                #deviation
                payload['db_lastblock']['spot_ma_deviation'][currency]=payload['db_lastblock']['pricing_record'][currency]/payload['db_lastblock']['pricing_spot_record'][currency]
                payload['db_lastblock24']['spot_ma_deviation'][currency]=payload['db_lastblock24']['pricing_record'][currency]/payload['db_lastblock24']['pricing_spot_record'][currency]

        payload['db_lastblock']['supply']=LastBlock['cumulative']['supply_offshore']
        payload['db_lastblock24']['supply']=LastBlock24['cumulative']['supply_offshore']
        

        
        
        #payload['db_lastblock']=LastBlock
        #payload['db_lastblock24']=LastBlock24
        
        resp.body =json.dumps(payload, ensure_ascii=False,default=json_util.default)
        resp.status=falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON

