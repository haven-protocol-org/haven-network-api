import falcon
from falcon_caching import Cache
cache = Cache(config={'CACHE_TYPE': 'simple'})

import json 
import libs.utils
import math
from datetime import datetime
from datetime import timezone
from dateutil.relativedelta import relativedelta

import mongodb

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from falcon_apispec import FalconPlugin
from marshmallow import Schema, fields

import calendar 


class CirculationSupplyResource:
    def __init__(self):
        self.mydb=mongodb.Mongodb()
        self.tools=libs.utils.tools()
        self.currencies=self.mydb.find("currencies")
    
    #@cache.cached(timeout=10)
    def on_get(self, req, resp):
        #If an end timestamp is specified, use this one, or timestamp=now()
        nbDatapoints=50
        if 'nbDatapoints' in req.params:
            nbDatapoints=int(req.params['nbDatapoints'])
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
        payload={'supply_coins':[],'ykeys':[],'ykeys_shore_fee':[],'ykeys_deviation_ratio':[],'ykeys_deviation':[],'organic_coins':[],'breakdown_coins':[],'supply_value':[],'organic_value':[],'breakdown_value':[],'deviation_ratio':[],'deviation':[],'offshore_fee':[]}
        
        
        for x in range(0,nbDatapoints+1):
            ts_target=ts_from + ((x)*ts_diff)
            dt_target=datetime.utcfromtimestamp(int(ts_target))
            TmpBlock={}
            TmpBlockOrganic={}
            TmpBlockOrganic['offshore']=0
            totalCoins=0

            TmpBlockValue={}
            TmpBlockOrganicValue={}
            TmpBlockOrganicValue['offshore']=0
            TmpBlockDeviationRatio={}
            TmpBlockDeviation={}
            OffShoreFee={}
            totalValue=0

            print ("Point  : " + str(x) +  " on "  + str(nbDatapoints))
            
            query={'header.timestamp':{'$lte':dt_target}}

            block=self.mydb.find_last("blocks",query)
            if block is not None:
                print (block['_id'])
                TmpBlock['period']=dt_target.strftime("%Y-%m-%d %H:%M")
                TmpBlockValue['period']=dt_target.strftime("%Y-%m-%d %H:%M")
                TmpBlockOrganic['period']=TmpBlock['period']
                TmpBlockOrganicValue['period']=TmpBlock['period']
                TmpBlockDeviationRatio['period']=TmpBlock['period']
                TmpBlockDeviationRatio['spot_price']=100
                TmpBlockDeviation['period']=TmpBlock['period']
                OffShoreFee['period']=TmpBlock['period']
                
                self.currencies.rewind()
                for currency in self.currencies:
                    TmpBlock[currency['xasset']]=round(block['cumulative']['supply_offshore'][currency['xasset']],4)
                    if currency['xasset']=='XHV':
                        TmpBlockValue[currency['xasset']]=round(block['cumulative']['supply_offshore'][currency['xasset']]*self.tools.convertFromMoneroFormat(block['pricing_spot_record']['xUSD']),4)
                    else:
                        TmpBlockValue[currency['xasset']]=TmpBlock[currency['xasset']]
                    totalCoins+=TmpBlock[currency['xasset']]
                    totalValue+=TmpBlockValue[currency['xasset']]

                    #Deviation
                    if currency['xasset']!='XHV' and block['header']['pricing_record'][currency['xasset']]!=0:
                        TmpBlockDeviationRatio[currency['xasset']]=round(block['header']['pricing_record'][currency['xasset']]/block['pricing_spot_record'][currency['xasset']]*100,4)
                        TmpBlockDeviation[currency['xasset'] + "-spot"]=round(self.tools.convertFromMoneroFormat(block['pricing_spot_record'][currency['xasset']]),4)
                        TmpBlockDeviation[currency['xasset'] + '-ma']=round(self.tools.convertFromMoneroFormat(block['header']['pricing_record'][currency['xasset']]),4)
                        BaseOffShoreFee=abs(block['header']['pricing_record'][currency['xasset']]-block['pricing_spot_record'][currency['xasset']])

                        OffShoreFee[currency['xasset']+'-high']=round(self.tools.convertFromMoneroFormat(BaseOffShoreFee*100),4)
                        OffShoreFee[currency['xasset']+'-medium']=round(self.tools.convertFromMoneroFormat(BaseOffShoreFee*77.11799083),4)
                        OffShoreFee[currency['xasset']+'-normal']=round(self.tools.convertFromMoneroFormat(BaseOffShoreFee*41.56808978),4)
                        OffShoreFee[currency['xasset']+'-low']=round(self.tools.convertFromMoneroFormat(BaseOffShoreFee*0.2897732758),4)

                        
                    if currency['xasset']=='XHV':
                        #Coins
                        TmpBlockOrganic['supply']=round(block['cumulative']['supply'][currency['xasset']],4)
                        TmpBlockOrganic['offshore']+=round(block['cumulative']['supply_offshore'][currency['xasset']],4)
                        #Value
                        TmpBlockOrganicValue['supply']=round(block['cumulative']['supply'][currency['xasset']]*self.tools.convertFromMoneroFormat(block['pricing_spot_record']['xUSD']),4)
                        TmpBlockOrganicValue['offshore']+=round(block['cumulative']['supply_offshore'][currency['xasset']]*self.tools.convertFromMoneroFormat(block['pricing_spot_record']['xUSD']),4)

                payload['supply_coins'].append(TmpBlock)
                payload['supply_value'].append(TmpBlockValue)
                payload['organic_coins'].append(TmpBlockOrganic)
                payload['organic_value'].append(TmpBlockOrganicValue)
                payload['deviation_ratio'].append(TmpBlockDeviationRatio)
                payload['deviation'].append(TmpBlockDeviation)
                payload['offshore_fee'].append(OffShoreFee)
                
        #Loading yKeys only with Supply>0
        self.currencies.rewind()
        payload['ykeys_deviation_ratio'].append('spot_price')
        for currency in self.currencies:
            if currency['xasset'] in TmpBlock and TmpBlock[currency['xasset']]>0:
                payload['ykeys'].append(currency['xasset'])
                if currency['xasset']!='XHV':
                    payload['ykeys_deviation_ratio'].append(currency['xasset'])
                    payload['ykeys_deviation'].append(currency['xasset']+ "-spot")
                    payload['ykeys_deviation'].append(currency['xasset']+ "-ma")
                    payload['ykeys_shore_fee'].append(currency['xasset']+ "-low")
                    payload['ykeys_shore_fee'].append(currency['xasset']+ "-normal")
                    payload['ykeys_shore_fee'].append(currency['xasset']+ "-medium")
                    payload['ykeys_shore_fee'].append(currency['xasset']+ "-high")

        self.currencies.rewind()
        for currency in self.currencies:
            donutBlock={}
            donutBlockValue={}
            if currency['xasset'] in TmpBlock and TmpBlock[currency['xasset']]>0:
                donutBlock['label']=currency['xasset']
                donutBlockValue['label']=currency['xasset']
                if currency['xasset']=='XHV':
                    donutBlock['value']=math.ceil((TmpBlock[currency['xasset']]/totalCoins)*100)
                    donutBlockValue['value']=math.ceil((TmpBlockValue[currency['xasset']]/totalValue)*100)
                else:
                    donutBlock['value']=math.floor((TmpBlock[currency['xasset']]/totalCoins)*100)
                    donutBlockValue['value']=math.floor((TmpBlockValue[currency['xasset']]/totalValue)*100)
                print (donutBlock)
                payload['breakdown_coins'].append(donutBlock)
                payload['breakdown_value'].append(donutBlockValue)
                
        

        print ("end : " +str (ts_to))
        #print (payload)
        resp.body = json.dumps(payload)
        resp.status=falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON

    