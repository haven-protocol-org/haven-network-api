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
    self.mydb= mongodb.Mongodb()
    self.currencies=self.mydb.find('currencies')
    self.tools = tools()

  def getInfo(self,coin):
    url=self.url+"coins/"+coin
    response=requests.request("get",url)
    return response
  def getlastrate(self,coin, currency):
    url=self.url+"simple/price?ids="+coin+ "&vs_currencies=" + currency
    response = requests.request("get", url)
    return response

  def importCurrencies(self):
    currencies={65:"XHV", 66:"xAG", 67:"xAU", 68:"xAUD", 69:"xBTC", 70:"xCAD", 71:"xCHF", 72:"xCNY", 73:"xEUR", 74:"xGBP", 75:"xJPY", 76:"xNOK", 77:"xNZD", 78:"xUSD"}
    currenciesConvert={'xhv':'xhv','xbtc':'btc','xusd':'usd','xag':"xag", 'xau':'xau', 'xaud':'aud', 'xcad':'cad','xchf':'chf', 'xcny':'cny', 'xeur':'eur', 'xgbp':'gbp', 'xjpy':'jpy', 'xnok':'nok', 'xnzd':'nzd'}
    for currency in currencies:
      mydict={}
      mydict['xasset']=currencies[currency]
      mydict['code']=currenciesConvert[currencies[currency].lower()]
      mydict['_id']=currency
      self.mydb.insert_one("currencies",mydict)

  def importExchangePrice(self,duration=30):
    self.currencies.rewind()
    print (self.currencies.count())
    for coin in self.currencies:
        if coin['code']=='xhv':
          continue
        print ("Import Currency : " + coin['code'] + " for the last " + str(duration) + " days.")
        url=self.url+ "coins/haven/market_chart?vs_currency=" + coin['code'] + "&days="+str(duration)
        print (url)
        response = requests.request("get", url)
        rates=json.loads(response.text)
        if 'prices' in rates:          
          for rate in rates['prices']:
            dt=datetime.utcfromtimestamp(int(str(rate[0])[:10]))
            #print (dt)
            dt=dt.replace(minute=0, second=0)
            #print (dt)
            ts=datetime.timestamp(dt)
            #We check on DB if a rates exists with this timestamp
            query={'_id': ts}
            foundRate=self.mydb.find_last("rates",query)
            if foundRate is not None:
              print ('rate found')
              #We update existing rates
              if foundRate['currencies_count']=>(self.currencies.count()-1):
                newvalues = { "$set": {'price_record.'  + coin['xasset']: self.tools.convertToMoneroFormat(rate[1])}}
              else:
                newvalues = { "$set": {'price_record.'  + coin['xasset']: self.tools.convertToMoneroFormat(rate[1])},'$inc':{'currencies_count':+1}}
              self.mydb.update_one("rates",query, newvalues)
            else:
              #we create the rate with the currency
              myRate={'price_record':{}}
              print ('no rate found')
              myRate['valid_from']=dt #datetime.utcfromtimestamp(int(str(rate[0])[:10]))
              myRate['price_record'][coin['xasset']]=self.tools.convertToMoneroFormat(rate[1])
              myRate['_id']=ts
              myRate['currencies_count']=1
              self.mydb.insert_one("rates",myRate)
        else:
          print ("No rates for " + coin['xasset'])
    return response