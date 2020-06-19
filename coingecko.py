import os
import requests
import json
import pymongo 
import math

class coingecko:
  def __init__(self):
    self.url='https://api.coingecko.com/api/v3/'
    self.coin='haven'
    self.currenciesConvert={'xhv':'xhv','xbtc':'btc','xusd':'usd','xag':"xag", 'xau':'xau', 'xaud':'aud', 'xcad':'cad','xchf':'chf', 'xcny':'cny', 'xeur':'eur', 'xgbp':'gbp', 'xjpy':'jpy', 'xnok':'nok', 'xnzd':'nzd'}
    
  def getlastrate(self,coin, currency):
    url=self.url+"simple/price?ids="+coin+ "&vs_currencies=" + currency
    response = requests.request("get", url)
    return response

  def importExchangePrice(self,duration=30):
    for coin in self.currenciesConvert:
        print ("Import Currency : " + self.currenciesConvert[coin])
        url=self.url+ "coins/haven/market_chart?vs_currency=" + self.currenciesConvert[coin] + "&days="+str(duration)
        response = requests.request("get", url)
        rates=json.loads(response.text)
        if 'prices' in rates:
          myclient = pymongo.MongoClient(os.environ['mongo'])
          mydb = myclient["haven"]
          RateCol = mydb["rates"]
          valid_from=0
          for rate in rates['prices']:
            myRate={}
            myRate['valid_from']=valid_from
            myRate['valid_until']=rate[0]
            myRate['from']='xhv'
            myRate['to']=coin
            myRate['rate']=self.convertToMonero(rate[1])
            myRate['_id']=str(rate[0])+"-"+coin
            valid_from=rate[0]
            try:
                RateCol.insert_one(myRate)
            except pymongo.errors.DuplicateKeyError:
                pass
            except Exception as e:
                print(type(e)) 
                print(e.args)
                print(e)
        else:
          print ("No rates for " + coin)


    return response
  def convertToMonero(self,floatNumber):
    floatNumber=floatNumber*pow(10,12)
    floatNumber=math.trunc(floatNumber)
    floatNumber=int(str(floatNumber)[:12])
    return floatNumber