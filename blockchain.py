import requests
import json
import math
import re
from mongodb import mongodb

class blockchain:
  def __init__(self):
    self.url="http://192.168.0.9:37750"
    self.currencies={65:"XHV", 66:"xAG", 67:"xAU", 68:"xAUD", 69:"xBTC", 70:"xCAD", 71:"xCHF", 72:"xCNY", 73:"xEUR", 74:"xGBP", 75:"xJPY", 76:"xNOK", 77:"xNZD", 78:"xUSD"}
    self.currenciesConvert={'xhv':'xhv','xbtc':'btc','xusd':'usd','xag':"ag", 'xau':'xau', 'xaud':'aud', 'xcad':'cad','xchf':'chf', 'xcny':'cny', 'xeur':'eur', 'xgbp':'gbp', 'xjpy':'jpy', 'xnok':'nok', 'xnzd':'nzd'}
    self.mydb = mongodb()
    
  def importCurrencies(self):
    for currency in self.currencies:
      mydict={}
      mydict['xasset']=self.currencies[currency]
      mydict['code']=self.currenciesConvert[self.currencies[currency].lower()]
      mydict['_id']=currency
      self.mydb.insert_one("currencies",mydict)
 
  def scanBlockchain(self):
    self.importCurrencies()
        
    #get Lastblock in blockchain
    response = self.getLastBlockHeader()
    if response['status_code']==200:
      lastBlock=response['text']['height']-1
      print ("Starting import on " + self.getNetworkName())
      print ("Blockchain height is " + str(lastBlock))
      
    #check the last block in DB
    restart=self.mydb.find_last("blocks")
    if restart is not None and '_id' in restart:
      restart=restart['_id']
    else:
      restart=0
    print ("DB height is " + str(restart))

    PreviousBlock=None
    #Always rescan blockchain - blocks to check if a reorg is happening
    if restart<=50:
      restart=0
    else:
      restart-=50
    for blockHeight in range(restart,lastBlock+1):
    #for blockHeight in range(0,50):
      print ("Import block " + str(blockHeight) + "/" + str(lastBlock))
      params={"height":blockHeight}
      block=self.getBlock(params)

      #Block header and ID
      myBlock={}
      myBlock['pricing_spot_record']={}
      myBlock['cumulative']={'supply':{},'supply_offshore':{}}

      myBlock['header']=block['text']['result']['block_header']
      myBlock['_id']=block['text']['result']['block_header']['height']

      #Check against DB the blockhash
      DBHash=self.mydb.find_one("blocks",{"_id": myBlock['_id']})

      if DBHash is not None and DBHash['header']['hash']!=myBlock['header']['hash']:
        print ("Reorganize on block " + str(myBlock['_id']))
        #We need to delete all block above _id
        self.mydb.delete("txs",{ "block_height": {"$gte": myBlock['_id']} })
        self.mydb.delete("blocks", {"_id": {"$gte": myBlock['_id']} })
        if myBlock['_id']+10<lastBlock:
          print ("Reorganize happening later. Maybe 51% attack")

      #Init for supply & offshore data
      for currency in self.currencies:
        myBlock['cumulative']['supply'][self.currencies[currency]]=0
        myBlock['cumulative']['supply_offshore'][self.currencies[currency]]=0
        myBlock['pricing_spot_record'][self.currencies[currency]]=0

      #Cumulative Supply
      myBlock=self.getCumulative(myBlock, PreviousBlock,block)
  
      for pricingRecord in myBlock['header']['pricing_record']:
        if isinstance(myBlock['header']['pricing_record'][pricingRecord],int) and myBlock['header']['pricing_record'][pricingRecord]>0 and pricingRecord.lower() in self.currenciesConvert:
          #Check for rate in RateDB
          query={'$and': [{'to': pricingRecord.lower()} , { 'valid_from': { '$lte': myBlock['header']['timestamp']*1000} } , { 'valid_until': { '$gte': myBlock['header']['timestamp']*1000} }]}
          rate=self.mydb.find_one("rates",query)
          if rate is not None:
            myBlock['pricing_spot_record'][pricingRecord]=rate['rate']
          else:
            print ("no rate for " + pricingRecord)

      #Transactions in Block
      if 'tx_hashes' in block['text']['result']:
        myBlock['tx_hashes']=block['text']['result']['tx_hashes']
        for tx in block['text']['result']['tx_hashes']:
          myTx=self.ParseTransaction(tx)
          myTx['block_hash']=myBlock['header']['hash']
          if myTx['amount_minted']>0 or myTx['amount_burnt']>0:
            myBlock['cumulative']['supply_offshore'][self.currencies[myTx['offshore_data'][0]]]-=myTx['amount_burnt']
            myBlock['cumulative']['supply_offshore'][self.currencies[myTx['offshore_data'][1]]]+=myTx['amount_minted']
            #Write tx data
            self.mydb.insert_one("txs",myTx)
 
      #Write Block data
      self.mydb.insert_one("blocks",myBlock)


      #Case for Timestamp on Block Genesis
      if myBlock['_id']==1:
        myquery = { "_id": 0 }
        newvalues = { "$set": { "header.timestamp": myBlock['header']['timestamp'], "pricing_spot_record":myBlock['pricing_spot_record'] } }
        self.mydb.update_one("blocks",myquery, newvalues)

      PreviousBlock=myBlock

  def getCumulative(self,myBlock,PreviousBlock,block):
    blockHeight=myBlock['_id']
    if blockHeight>0:
      if PreviousBlock is None:
        PreviousBlock=self.mydb.find_one("blocks",{'_id':blockHeight-1})
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
    myTx['hash']=tx
    myTx['pricing_record_height']=transactionJson['pricing_record_height']
    myTx['offshore_data']=transactionJson['offshore_data']
    myTx['amount_burnt']=transactionJson['amount_burnt']
    myTx['amount_minted']=transactionJson['amount_minted']
    myTx['block_height']=transaction['text']['txs'][0]['block_height']
    myTx['block_timestamp']=transaction['text']['txs'][0]['block_timestamp']
    myTx['_id']=tx
    return myTx
  
  def getInfo(self):
    return self.callDeamonJsonRPC("POST","get_info")
  def isMainnet(self):
    info=self.getInfo()
    return info['text']['result']['mainnet']

  def isStagenet(self):
    info=self.getInfo()
    return info['text']['result']['stagenet']
  
  def isTestnet(self):
    info=self.getInfo()
    return info['text']['result']['testnet']
  
  def getNetworkName(self):
    if self.isMainnet():
      return "Mainnet"
    if self.isStagenet():
      return "Stagenet"
    if self.isTestnet():
      return "Testnet"
    return "Network unknown"

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
      extract=re.sub('signature": ".*[^a-zA-Z0-9].*",','signature": "",',response.text)
      callback['text']=json.loads(extract)
    except Exception as e:
      print (e)
      print (response.text)
      print (extract)
      callback['text']=response.text
    
    return callback