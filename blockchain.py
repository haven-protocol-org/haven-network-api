import os
import requests
import json
import pymongo 
import math

class blockchain:
  def __init__(self):
    self.url="http://192.168.0.9:37750"
    self.currencies={65:"XHV", 66:"xAG", 67:"xAU", 68:"xAUD", 69:"xBTC", 70:"xCAD", 71:"xCHF", 72:"xCNY", 73:"xEUR", 74:"xGBP", 75:"xJPY", 76:"xNOK", 77:"xNZD", 78:"xUSD"}
    self.currenciesConvert={'xhv':'xhv','xbtc':'btc','xusd':'usd','xag':"ag", 'xau':'xau', 'xaud':'aud', 'xcad':'cad','xchf':'chf', 'xcny':'cny', 'xeur':'eur', 'xgbp':'gbp', 'xjpy':'jpy', 'xnok':'nok', 'xnzd':'nzd'}
    self.myclient = pymongo.MongoClient(os.environ['mongo'])
    self.mydb = self.myclient["haven"]
    self.BlockCol = self.mydb["blocks"]
    self.TxCol=self.mydb["txs"]
    self.RateCol=self.mydb["rates"]
    self.CurrencyCol=self.mydb["currencies"]

  def importCurrencies(self):
    for currency in self.currencies:
      mydict={}
      mydict['xasset']=self.currencies[currency]
      mydict['code']=self.currenciesConvert[self.currencies[currency].lower()]
      mydict['_id']=currency
      try:
        self.CurrencyCol.insert_one(mydict)
      except pymongo.errors.DuplicateKeyError:
        pass
      except Exception as e:
        print(type(e)) 
        print(e.args)
        print(e) 

  def scanBlockchain(self):
    self.importCurrencies()
        
    #get Lastblock in blockchain
    response = self.getLastBlockHeader()
    if response['status_code']==200:
      lastBlock=response['text']
      print ("Blockchain height is " + str(lastBlock['height']))
      
    #check the last block in DB
    restart=self.mydb.blocks.find_one(sort=[( '_id', pymongo.DESCENDING )])
    if restart is not None and '_id' in restart:
      restart=restart['_id']
    else:
      restart=0
    print ("DB height is " + str(restart))

    PreviousBlock=None
    for blockHeight in range(restart,lastBlock['height']+1):
    #for blockHeight in range(0,3):
      print ("Import block " + str(blockHeight) + "/" + str(lastBlock['height']))
      params={"height":blockHeight}
      block=self.getBlock(params)

      myBlock={}
      myBlock['pricing_spot_record']={}
      myBlock['cumulative']={'supply':{},'supply_offshore':{}}

      #Init for supply & offshore data
      for currency in self.currencies:
        myBlock['cumulative']['supply'][self.currencies[currency]]=0
        myBlock['cumulative']['supply_offshore'][self.currencies[currency]]=0
        myBlock['pricing_spot_record'][self.currencies[currency]]=0

      #Block header and ID
      myBlock['header']=block['text']['result']['block_header']
      myBlock['_id']=block['text']['result']['block_header']['height']

      #Cumulative Supply
      myBlock=self.getCumulative(myBlock, PreviousBlock,block)
  
      for pricingRecord in myBlock['header']['pricing_record']:
        if isinstance(myBlock['header']['pricing_record'][pricingRecord],int) and myBlock['header']['pricing_record'][pricingRecord]>0 and pricingRecord.lower() in self.currenciesConvert:
          #Check for rate in RateDB
          query={'$and': [{'to': pricingRecord.lower()} , { 'valid_from': { '$lte': myBlock['header']['timestamp']} } , { 'valid_until': { '$gte': myBlock['header']['timestamp']} }]}
          rate=self.mydb.rates.find_one(query)
          if rate is not None:
            myBlock['pricing_spot_record'][pricingRecord]=rate['rate']
          else:
            print ("no rate for " + pricingRecord)

      #Transactions in Block
      if 'tx_hashes' in block['text']['result']:
        myBlock['tx_hashes']=block['text']['result']['tx_hashes']
        for tx in block['text']['result']['tx_hashes']:
          myTx=self.ParseTransaction(tx)        
          if myTx['amount_minted']>0 or myTx['amount_burnt']>0:
            myBlock['cumulative']['supply_offshore'][self.currencies[myTx['offshore_data'][0]]]-=myTx['amount_burnt']
            myBlock['cumulative']['supply_offshore'][self.currencies[myTx['offshore_data'][1]]]+=myTx['amount_minted']
            
          #Write Transaction data
          try:
            self.TxCol.insert_one(myTx)
          except pymongo.errors.DuplicateKeyError:
            pass
          except Exception as e:
            print(type(e)) 
            print(e.args)
            print(e) 
            
      #Write Block data
      try:
        self.BlockCol.insert_one(myBlock)
      except pymongo.errors.DuplicateKeyError:
        pass
      except Exception as e:
        print(type(e)) 
        print(e.args)
        print(e) 
      
      #Case for Timestamp on Block Genesis
      if myBlock['_id']==1:
        myquery = { "_id": 0 }
        newvalues = { "$set": { "header.timestamp": myBlock['header']['timestamp'], "pricing_spot_record":myBlock['pricing_spot_record'] } }
        print (newvalues)
        self.BlockCol.update_one(myquery, newvalues)

      PreviousBlock=myBlock
  
  def getCumulative(self,myBlock,PreviousBlock,block):
    blockHeight=myBlock['_id']
    if blockHeight>0:
      if PreviousBlock is None:
        PreviousBlock=self.mydb.blocks.find_one({'_id':blockHeight-1})
      for currency in self.currencies:
        #loop to get all cumulative supply from previousBlock
        myBlock['cumulative']['supply'][self.currencies[currency]]=PreviousBlock['cumulative']['supply'][self.currencies[currency]]
        myBlock['cumulative']['supply_offshore'][self.currencies[currency]]=PreviousBlock['cumulative']['supply_offshore'][self.currencies[currency]]

    myBlock['cumulative']['supply'][self.currencies[65]]+=block['text']['result']['block_header']['reward']
    myBlock['cumulative']['supply_offshore'][self.currencies[65]]+=block['text']['result']['block_header']['reward']
    return myBlock

  def ParseTransaction(self,tx):
    paramsTx={"txs_hashes":[tx],"decode_as_json":True}
    transaction=self.getTransaction(paramsTx)
    transactionTxt=''.join(transaction['text']['txs_as_json'])
    transactionJson=json.loads(transactionTxt)
    myTx={}
    myTx['pricing_record_height']=transactionJson['pricing_record_height']
    myTx['offshore_data']=transactionJson['offshore_data']
    myTx['amount_burnt']=transactionJson['amount_burnt']
    myTx['amount_minted']=transactionJson['amount_minted']
    myTx['block_height']=transaction['text']['txs'][0]['block_height']
    myTx['block_timestamp']=transaction['text']['txs'][0]['block_timestamp']
    myTx['_id']=tx
    return myTx


  def getLastBlockHeader(self):
    return self.callDeamonRPC("POST","get_height")

  def getBlockHeaderByHeight(self,params):
    return self.callDeamonJsonRPC("POST","get_block_header_by_height",params)

  def getTransaction(self,params):
    return self.callDeamonRPC("POST","gettransactions",params)

  def getBlock(self,params):
    return self.callDeamonJsonRPC("POST","get_block",params)

  def callDeamonJsonRPC(self,verb,method,params=""):
      data={"jsonrpc":"2.0","id":"0","method":method}
      if params:
        data['params']=params
      query="json_rpc"
      return self.callDeamonRPC(verb,query,data)

  def callDeamonRPC(self,verb, query, data=""):
    callback={}
    headers={'Content-Type': 'application/json'}
    if data:
      response = requests.request(verb, self.url + "/" + query, data=json.dumps(data), headers=headers)
    else:
      response = requests.request(verb, self.url + "/" + query, headers=headers)    
    callback['status_code']=response.status_code
    try:
      callback['text']=json.loads(response.text,strict=False)
    except Exception as e:
      print (e)
      callback['text']=response.text
    
    return callback