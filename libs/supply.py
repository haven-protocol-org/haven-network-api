import falcon
import json 
import libs.utils
import math
from datetime import datetime
from datetime import timezone
from dateutil.relativedelta import relativedelta

from mongodb import mongodb

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from falcon_apispec import FalconPlugin
from marshmallow import Schema, fields

import calendar 

class SupplyResource:
    def __init__(self):
        self.mydb=mongodb()
    def on_get(self, req, resp):
        """Get current supply on blockchain.
        ---
        description: Get current supply on blockchain
        responses:
            200:
                description: Supply for all xAssets and XHV will be return
                schema: SupplySchema
        """
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
        response['prices']=block['cumulative']
        response['timestamp']=timestamp
        response['block_timestamp']=block['header']['timestamp']
        
        resp.body = json.dumps(response)
        resp.status=falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON


class SupplySchema(Schema):
    id = fields.Int()
    name = fields.Str(required=True)



class CirculationSupplyResource:
    def __init__(self):
        self.mydb=mongodb()
        self.tools=libs.utils.tools()
        self.currencies=self.mydb.find("currencies")
    def on_get(self, req, resp):
        #If an end timestamp is specified, use this one, or timestamp=now()
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
        payload={'data':[],'ykeys':[],'organic':[],'donut':[]}
        for currency in self.currencies:
            payload['ykeys'].append("'" + currency['xasset'] + "'" )
        
        for x in range(0,nbDatapoints+1):
            ts_target=ts_from + ((x)*ts_diff)
            dt_target=datetime.utcfromtimestamp(int(ts_target))
            TmpBlock={}
            TmpBlockOrganic={}
            TmpBlockOrganic['offshore']=0
            totalCoins=0
            print ("Point  : " + str(x) +  " on "  + str(nbDatapoints))
            
            query={'header.timestamp':{'$lte':dt_target}}

            block=self.mydb.find_last("blocks",query)
            if block is not None:
                TmpBlock['period']=dt_target.strftime("%Y-%m-%d %H:%M")
                TmpBlockOrganic['period']=TmpBlock['period']
                self.currencies.rewind()
                for currency in self.currencies:
                    TmpBlock[currency['xasset']]=self.tools.calcMoneroPow(block['cumulative']['supply_offshore'][currency['xasset']])
                    totalCoins+=TmpBlock[currency['xasset']]
                    if currency['xasset']=='XHV':
                        TmpBlockOrganic['supply']=self.tools.calcMoneroPow(block['cumulative']['supply'][currency['xasset']])
                        TmpBlockOrganic['offshore']+=self.tools.calcMoneroPow(block['cumulative']['supply_offshore'][currency['xasset']])

                payload['data'].append(TmpBlock)
                payload['organic'].append(TmpBlockOrganic)

        self.currencies.rewind()
        for currency in self.currencies:
            donutBlock={}
            if currency['xasset'] in TmpBlock and TmpBlock[currency['xasset']]>0:
                donutBlock['label']=currency['xasset']
                if currency['xasset']=='XHV':
                    donutBlock['value']=math.ceil((TmpBlock[currency['xasset']]/totalCoins)*100)
                else:
                    donutBlock['value']=math.floor((TmpBlock[currency['xasset']]/totalCoins)*100)
                print (donutBlock)
                payload['donut'].append(donutBlock)
        
        
        print ("end : " +str (ts_to))
        #print (payload)
        resp.body = json.dumps(payload)
        resp.status=falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON

    