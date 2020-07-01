import falcon
from falcon_caching import Cache
cache = Cache(config={'CACHE_TYPE': 'simple'})

import json 
import libs.utils
from datetime import datetime
from datetime import timezone
from dateutil.relativedelta import relativedelta

import mongodb

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from falcon_apispec import FalconPlugin
from marshmallow import Schema, fields

import calendar


class DeviationHistoryResource:
    def __init__(self):
        self.mydb=mongodb.Mongodb()
        self.tools=libs.utils.tools()
    
    @cache.cached(timeout=10)
    def on_get(self, req, resp):
        #If an end timestamp is specified, use this one, or timestamp=now()
        currency=req.params['currency']
        currency=self.mydb.find_one("currencies",{'code': currency.lower()})
        currency=currency['xasset']
        nbDatapoints=50
        dt_to = datetime.now()
        if 'to' in req.params:
          try:
              dt_to = datetime.utcfromtimestamp(int(req.params['to']))
          except TypeError as e:
              #Timestamp not valid, revert to now()
              print (e)
              
          except Exception:
              resp.status=falcon.HTTP_401
              return 
        #if a start timestamp is specified, use this one, or from is to-1 year
        dt_from = dt_to - relativedelta(months=1)
        if 'from' in req.params:
          try:
              dt_from = datetime.utcfromtimestamp(int(req.params['from']))
          except TypeError as e:
              #Timestamp not valid, revert to now()
              print (e)

          except Exception:
              resp.status=falcon.HTTP_401
              return 
        ts_to=calendar.timegm(dt_to.timetuple())
        ts_from=calendar.timegm(dt_from.timetuple())
        #We need ~100 pts of data, so each points will be seperated by ts_diff/100
        ts_diff = (ts_to-ts_from)/nbDatapoints #time elasped between start & end.
        print ("start : " +str (ts_from))
        payload=[]
        
        for x in range(0,nbDatapoints):
            ts_target=ts_from + ((x)*ts_diff)
            dt_target=datetime.utcfromtimestamp(int(ts_target))
            TmpBlock={}
            print ("Point  : " + str(x) +  " " + str(ts_target))
            query={'header.timestamp':{'$lte':dt_target}}
            block=self.mydb.find_last("blocks",query)
            if block is not None:
                TmpBlock['period']=datetime.utcfromtimestamp(ts_target).strftime("%Y-%m-%d %H:%M")
                TmpBlock['spot_price']=self.tools.convertFromMoneroFormat(block['pricing_spot_record'][currency],currency)
                TmpBlock['ma_price']=self.tools.convertFromMoneroFormat(block['header']['pricing_record'][currency],currency)
                payload.append(TmpBlock)
            #print (block)

        print ("end : " +str (ts_to))
        #print (payload)

        resp.body = json.dumps(payload)
        resp.status=falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON

