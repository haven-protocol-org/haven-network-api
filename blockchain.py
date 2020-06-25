import requests
import json
import math
import re
import os
import mongodb
from datetime import datetime
from libs.utils import tools
class Blockchain:
  def __init__(self):
    self.url=os.environ['daemon_url']
    self.mydb = mongodb.Mongodb()
    self.utils = tools()
    self.currencies=self.mydb.find("currencies")
    self.xhv=self.mydb.find_one("currencies",{'code':'xhv'})
    
  def scanBlockchain(self):       
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
    #for blockHeight in range(0,100):
      print ("Import block " + str(blockHeight) + "/" + str(lastBlock))
      params={"height":blockHeight}
      block=self.getBlock(params)

      #Block header and ID
      myBlock={}
      myBlock['pricing_spot_record']={}
      myBlock['cumulative']={'supply':{},'supply_offshore':{}}

      myBlock['header']=block['text']['result']['block_header']
      myBlock['header']['timestamp']=datetime.utcfromtimestamp(myBlock['header']['timestamp'])
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
      self.currencies.rewind()
      for currency in self.currencies:
        myBlock['cumulative']['supply'][currency['xasset']]=0
        myBlock['cumulative']['supply_offshore'][currency['xasset']]=0
        myBlock['pricing_spot_record'][currency['xasset']]=0
      #Cumulative Supply
      myBlock=self.getCumulative(myBlock, PreviousBlock,block)
      #if 'pricing_record' in myBlock['header']:
      #  for pricingRecord in myBlock['header']['pricing_record']:
      
      self.currencies.rewind()
      for currency in self.currencies:
        #Check for rate in RateDB
        if currency['code']!='xhv':
          query={'$and': [{'to': currency['code'] } , { 'valid_from': { '$lte': myBlock['header']['timestamp']} }]}
          rate=self.mydb.find_last("rates",query)
          if rate is not None:
            myBlock['pricing_spot_record'][currency['xasset']]=rate['rate']
          else:
            print ("no rate for " + currency['code'])
      #Transactions in Block
      if 'tx_hashes' in block['text']['result']:
        myBlock['tx_hashes']=block['text']['result']['tx_hashes']
        for tx in block['text']['result']['tx_hashes']:
          myTx=self.ParseTransaction(tx)
          myTx['block_hash']=myBlock['header']['hash']
          if ('amount_minted' in myTx and myTx['amount_minted']>0) or ('amount_burnt' in myTx and myTx['amount_burnt']>0):
            CurFrom=self.mydb.find_one("currencies",{'_id': myTx['offshore_data'][0]})
            CurTo=self.mydb.find_one("currencies",{'_id': myTx['offshore_data'][1]})
            myBlock['cumulative']['supply_offshore'][CurFrom['xasset']]-=self.utils.convertFromMoneroFormat(myTx['amount_burnt'])
            myBlock['cumulative']['supply_offshore'][CurTo['xasset']]+=self.utils.convertFromMoneroFormat(myTx['amount_minted'])
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
      self.currencies.rewind()
      for currency in self.currencies:
        #loop to get all cumulative supply from previousBlock
        myBlock['cumulative']['supply'][currency['xasset']]=PreviousBlock['cumulative']['supply'][currency['xasset']]
        myBlock['cumulative']['supply_offshore'][currency['xasset']]=PreviousBlock['cumulative']['supply_offshore'][currency['xasset']]
  
    myBlock['cumulative']['supply'][self.xhv['xasset']]+=self.utils.convertFromMoneroFormat(block['text']['result']['block_header']['reward'])
    myBlock['cumulative']['supply_offshore'][self.xhv['xasset']]+=self.utils.convertFromMoneroFormat(block['text']['result']['block_header']['reward'])

    return myBlock

  def ParseTransaction(self,tx):
    paramsTx={"txs_hashes":[tx],"decode_as_json":True}
    transaction=self.getTransaction(paramsTx)
    transactionTxt=''.join(transaction['text']['txs_as_json'])
    transactionJson=json.loads(transactionTxt)
    
    myTx={}
    myTx['hash']=tx
    if 'pricing_record_height' in transactionJson:
      myTx['pricing_record_height']=transactionJson['pricing_record_height']
    if 'offshore_data' in transactionJson:
      myTx['offshore_data']=transactionJson['offshore_data']
    if 'amount_burnt' in transactionJson:
      myTx['amount_burnt']=transactionJson['amount_burnt']
    if 'amount_minted' in transactionJson:
      myTx['amount_minted']=transactionJson['amount_minted']

    myTx['block_height']=transaction['text']['txs'][0]['block_height']
    myTx['block_timestamp']=datetime.utcfromtimestamp(transaction['text']['txs'][0]['block_timestamp'])
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