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
    try:
      response=requests.request("get",url, timeout=2)
      if response.status_code==200:
        f = open("/tmp/" + coin + ".json", "w")
        f.write(response.text)
        f.close()
        response = response.text
      else:
        raise Exception('wrong status code')
    except:
      f = open("/tmp/" + coin + ".json", "r")
      response=f.read()
    

    return response
  def getlastrate(self,coin, currency):
    url=self.url+"simple/price?ids="+coin+ "&vs_currencies=" + currency
    response = requests.request("get", url, timeout=5)
    return response

  def importCurrencies(self):
    currencies={65:"XHV", 66:"xAG", 67:"xAU", 68:"xAUD", 69:"xBTC", 70:"xCAD", 71:"xCHF", 72:"xCNY", 73:"xEUR", 74:"xGBP", 75:"xJPY", 76:"xNOK", 77:"xNZD", 78:"xUSD"}
    currenciesConvert={'xhv':'xhv','xbtc':'btc','xusd':'usd','xag':"xag", 'xau':'xau', 'xaud':'aud', 'xcad':'cad','xchf':'chf', 'xcny':'cny', 'xeur':'eur', 'xgbp':'gbp', 'xjpy':'jpy', 'xnok':'nok', 'xnzd':'nzd'}
    for currency in currencies:
      mydict={}
      mydict['xasset']=currencies[currency]
      print (currencies[currency])
      mydict['xassetcase']=currencies[currency].upper()
      mydict['code']=currenciesConvert[currencies[currency].lower()]
      mydict['_id']=currency
      self.mydb.insert_one("currencies",mydict)

  def importExchangePrice(self,duration=30,granularity='days'):
    self.currencies.rewind()
    print (self.currencies.count())
    #retrieving value for BTC
    
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    url=self.url+ "coins/bitcoin/market_chart?vs_currency=usd&days="+str(duration)
    response = requests.request("get", url, headers=headers)
    rates=json.loads(response.text)
    if 'prices' in rates:
      for rate in rates['prices']:
        dt=datetime.utcfromtimestamp(int(str(rate[0])[:10]))
        dt=dt.replace(minute=math.floor(dt.minute/10)*10 ,second=0)
        ts=datetime.timestamp(dt)
        #We check on DB if a rates exists with this timestamp
        query={'_id': ts}
        foundRate=self.mydb.find_last("rates",query)
        if foundRate is not None:
          #We update existing rates
          if 'xBTC' in foundRate['price_record']:
            newvalues = { "$set": {'price_record.xBTC': self.tools.convertToMoneroFormat(1/rate[1])}}
          else:
            newvalues = { "$set": {'price_record.xBTC': self.tools.convertToMoneroFormat(1/rate[1])},'$inc':{'currencies_count':+1}}
          self.mydb.update_one("rates",query, newvalues)
        else:
          #we create the rate with the currency
          myRate={'price_record':{}}
          print ('no rate found')
          myRate['valid_from']=dt #datetime.utcfromtimestamp(int(str(rate[0])[:10]))
          myRate['price_record']['xBTC']=self.tools.convertToMoneroFormat(1/rate[1])
          myRate['_id']=ts
          myRate['currencies_count']=1
          self.mydb.insert_one("rates",myRate)
    #retrieving value for XHV
    url=self.url+ "coins/haven/market_chart?vs_currency=usd&days="+str(duration)
    response = requests.request("get", url, headers=headers)
    rates=json.loads(response.text)
    if 'prices' in rates:
      for rate in rates['prices']:
        dt=datetime.utcfromtimestamp(int(str(rate[0])[:10]))
        dt=dt.replace(minute=math.floor(dt.minute/10)*10 ,second=0)
        ts=datetime.timestamp(dt)
        #We check on DB if a rates exists with this timestamp
        query={'_id': ts}
        foundRate=self.mydb.find_last("rates",query)
        if foundRate is not None:
          if 'xUSD' not in foundRate['price_record'] or foundRate['price_record']['xUSD']==0:
            newvalues = { "$set": {'price_record.xUSD': self.tools.convertToMoneroFormat(rate[1])},'$inc':{'currencies_count':+1}}
            self.mydb.update_one("rates",query, newvalues)
        else:
          #we create the rate with the currency
          myRate={'price_record':{}}
          print ('no rate found')
          myRate['valid_from']=dt #datetime.utcfromtimestamp(int(str(rate[0])[:10]))
          myRate['price_record']['xUSD']=self.tools.convertToMoneroFormat(rate[1])
          myRate['_id']=ts
          myRate['currencies_count']=1
          self.mydb.insert_one("rates",myRate)
    #We use the previous rate found and query the forex API
    PreviousdateStr=""
    if 'prices' in rates:
      for rate in rates['prices']:
        dt=datetime.utcfromtimestamp(int(str(rate[0])[:10]))
        dt=dt.replace(minute=math.floor(dt.minute/10)*10 ,second=0)
        ts=datetime.timestamp(dt)
        dateStr = dt.strftime("%Y-%m-%d")
        if dateStr!=PreviousdateStr:
          url= "https://api.ratesapi.io/api/"+ dateStr +"?base=USD&symbols=AUD,CAD,CHF,CNY,EUR,GBP,JPY,NOK,NZD"
          response = requests.request("get", url)
          exchangesRates=json.loads(response.text)
          PreviousdateStr=dateStr
        #We check on DB if a rates exists with this timestamp
        query={'_id': ts}
        foundRate=self.mydb.find_last("rates",query)
    
        for exchangeRate in exchangesRates['rates']:
          xasset="x" + exchangeRate.upper()
          print (exchangeRate)
          print (exchangesRates['rates'][exchangeRate])

          if foundRate is not None:
            #We update existing rates
            if xasset not in foundRate['price_record'] or foundRate['price_record'][xasset]==0:
              newvalues = { "$set": {'price_record.' + xasset: self.tools.convertToMoneroFormat(exchangesRates['rates'][exchangeRate])},'$inc':{'currencies_count':+1}}
              self.mydb.update_one("rates",query, newvalues)
              print (newvalues)
          else:
            #we create the rate with the currency
            myRate={'price_record':{}}
            print ('no rate found')
            myRate['valid_from']=dt #datetime.utcfromtimestamp(int(str(rate[0])[:10]))
            myRate['price_record'][xasset]=self.tools.convertToMoneroFormat(exchangesRates['rates'][exchangeRate])
            myRate['_id']=ts
            myRate['currencies_count']=1
            self.mydb.insert_one("rates",myRate)
            print (myRate)
    
    
    #We use the previous rate found and query the metal API
    PreviousdateStr=""
    if 'prices' in rates:
      for rate in rates['prices']:
        dt=datetime.utcfromtimestamp(int(str(rate[0])[:10]))
        dt=dt.replace(minute=math.floor(dt.minute/10)*10 ,second=0)
        ts=datetime.timestamp(dt)
        dateStr = dt.strftime("%Y-%m-%d")
        if dateStr!=PreviousdateStr:
          headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
          url="https://data-asg.goldprice.org/dbXRates/USD"
          response = requests.request("get", url, headers=headers)
          print (response.text)
          exchangesRate=json.loads(response.text)
          PreviousdateStr=dateStr
        #We check on DB if a rates exists with this timestamp
        query={'_id': ts}
        foundRate=self.mydb.find_last("rates",query)
        
        xasset=exchangeRate.upper()

        if foundRate is not None:
          print (foundRate)
          #We update existing rates
          if 'xAU' not in foundRate['price_record'] or foundRate['price_record']['xAU']==0:
            newvalues = { "$set": {'price_record.xAU': self.tools.convertToMoneroFormat(exchangesRate['items'][0]['xauPrice'])},'$inc':{'currencies_count':+1}}
            self.mydb.update_one("rates",query, newvalues)
          if 'xAG' not in foundRate['price_record'] or foundRate['price_record']['xAG']==0:
            newvalues = { "$set": {'price_record.xAG': self.tools.convertToMoneroFormat(exchangesRate['items'][0]['xagPrice'])},'$inc':{'currencies_count':+1}}
            self.mydb.update_one("rates",query, newvalues)
        else:
          #we create the rate with the currency
          myRate={'price_record':{}}
          print ('no rate found')
          myRate['valid_from']=dt #datetime.utcfromtimestamp(int(str(rate[0])[:10]))
          myRate['price_record']['xAU']=self.tools.convertToMoneroFormat(exchangesRate['items'][0]['xauPrice'])
          myRate['price_record']['xAG']=self.tools.convertToMoneroFormat(exchangesRate['items'][0]['xagPrice'])
          myRate['_id']=ts
          myRate['currencies_count']=1
          self.mydb.insert_one("rates",myRate)

    return response
