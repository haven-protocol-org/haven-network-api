import os
import requests
import json
import math
import mongodb
from datetime import datetime
from libs.utils import tools

class Coingecko:
  def __init__(self):
    self.url='https://api.coingecko.com/api/v3/'
    self.coin='haven'
    self.currenciesConvert={'xhv':'xhv','xbtc':'btc','xusd':'usd','xag':"xag", 'xau':'xau', 'xaud':'aud', 'xcad':'cad','xchf':'chf', 'xcny':'cny', 'xeur':'eur', 'xgbp':'gbp', 'xjpy':'jpy', 'xnok':'nok', 'xnzd':'nzd'}
    self.mydb= mongodb.Mongodb()
    self.tools = tools()

  def getlastrate(self,coin, currency):
    url=self.url+"simple/price?ids="+coin+ "&vs_currencies=" + currency
    response = requests.request("get", url)
    return response

  def importExchangePrice(self,duration=30):
    for coin in self.currenciesConvert:
        print ("Import Currency : " + self.currenciesConvert[coin] + " for the last " + str(duration) + " days.")
        url=self.url+ "coins/haven/market_chart?vs_currency=" + self.currenciesConvert[coin] + "&days="+str(duration)
        response = requests.request("get", url)
        rates=json.loads(response.text)
        if 'prices' in rates:
          query = {'$and': [{'to':coin}, {'valid_until':{'$lt': next(iter(rates['prices']))[0] }}] }
          lastRate=self.mydb.find_last("rates",query)
          valid_from=0
          if lastRate is not None:
            valid_from=lastRate['valid_until']
          for rate in rates['prices']:
            myRate={}
            myRate['valid_from']=datetime.utcfromtimestamp(valid_from)
            myRate['valid_until']=datetime.utcfromtimestamp(int(str(rate[0])[:10]))
            myRate['from']='xhv'
            myRate['to']=coin
            myRate['rate']=self.tools.convertToMoneroFormat(rate[1])
            myRate['_id']=str(rate[0])+"-"+coin
            valid_from=int(str(rate[0])[:10])
            self.mydb.insert_one("rates",myRate)
        else:
          print ("No rates for " + coin)


    return response
 