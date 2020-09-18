import requests
import json
import math
import re
import os
import mongodb
import libs.twitter
import pymongo
from datetime import datetime
from libs.utils import tools
class Blockchain:
  def __init__(self):
    self.url=os.environ['hv_daemon_url']
    self.mydb = mongodb.Mongodb()
    self.utils = tools()
    self.currencies=self.mydb.find("currencies")
    self.xhv=self.mydb.find_one("currencies",{'code':'xhv'})
    if 'hv_consumer_key' in os.environ:
      self.twitter=libs.twitter.Twitter(consumer_key=os.environ['hv_consumer_key'],
        consumer_secret=os.environ['hv_consumer_secret'],
        access_token_key=os.environ['hv_access_token_key'],
        access_token_secret=os.environ['hv_access_token_secret'])
    self.network=self.getInfo()['text']['result']['nettype']
    if self.network=='mainnet':
      self.offshore_activate_height=640600
    if self.network=='stagenet' or self.network=='testnet':
      self.offshore_activate_height=0
    
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
      restart=restart['_id']+1
    else:
      restart=-1

    #Search for a reorganize
    scanHop=1
    finished = False
    while not finished:
      BlockRestart=restart-scanHop
      if BlockRestart<0:
         BlockRestart=-1
      blockDB=self.mydb.find_last("blocks",{"_id":BlockRestart-1})
      BlockBC=self.getBlockHeaderByHeight({"height":BlockRestart-1})
      if blockDB is None or ('result' in BlockBC['text'] and blockDB['header']['hash']==BlockBC['text']['result']['block_header']['hash']):
        print ("Block " + str(BlockRestart) + " hash matches DB")
        finished=True
      else:
        print ("Reorganize on block " + str(BlockRestart) + " continue revert to find matching hash.")
        #Delete all the BC >= BlockRestart
        print ("Deleting DB from block " + str(BlockRestart-scanHop+1))
        self.mydb.delete("txs",{ "block_height": {"$gte": BlockRestart-scanHop+1} })
        self.mydb.delete("blocks", {"_id": {"$gte": BlockRestart-scanHop+1} })
      scanHop=scanHop*2

    print ("DB height is " + str(BlockRestart))

    PreviousBlock=None
    for blockHeight in range(BlockRestart+1,lastBlock+1):
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

      query={'$and':[{'valid_from': { '$lte': myBlock['header']['timestamp']}},{'currencies_count':13}]}
      
      rate=self.mydb.find_last("rates",query)
      if rate is None:
        rate=self.mydb.find_first("rates")
      
      myBlock['pricing_spot_record']=rate['price_record']

      #Transactions in Block#Transactions in Block
      if 'tx_hashes' in block['text']['result']:
        myBlock['tx_hashes']=block['text']['result']['tx_hashes']
      if 'tx_hashes' in block['text']['result'] and blockHeight>self.offshore_activate_height:
        for tx in block['text']['result']['tx_hashes']:
          myTx=self.ParseTransaction(tx)
          myTx['block_hash']=myBlock['header']['hash']
          if ('amount_minted' in myTx and myTx['amount_minted']>0) or ('amount_burnt' in myTx and myTx['amount_burnt']>0):
            CurFrom=self.mydb.find_one("currencies",{'_id': myTx['offshore_data'][0]})
            CurTo=self.mydb.find_one("currencies",{'_id': myTx['offshore_data'][1]})
            amountFrom=self.utils.convertFromMoneroFormat(myTx['amount_burnt'])
            amountTo=self.utils.convertFromMoneroFormat(myTx['amount_minted'])
            
            if hasattr(self,'twitter') and amountTo>10000:
              message='💵💵💵💵💵💵💵💵💵💵💵💵💵 \n\r\n\r{} ${} minted in exchange of {} ${}'.format(amountTo,CurTo['xasset'],amountFrom,CurFrom['xasset'])
              print (message)
              self.twitter.tweet(message)
            if hasattr(self,'twitter') and self.mydb.count('txs')==0:
              #First User
              message='🎉🎉🎉🎉🎉 Congrats to our first user 🎉🎉🎉🎉🎉\n\r\n\r💵💵💵💵💵💵💵💵💵💵💵💵💵 \n\r{} ${} minted in exchange of {} ${}'.format(amountTo,CurTo['xasset'],amountFrom,CurFrom['xasset'])
              print (message)
              self.twitter.tweet(message)

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
    if blockHeight>1:
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

    myTx['unlock_time']=transactionJson['unlock_time']
    myTx['priority']="N/A"
    AbsoluteUnlock=myTx['unlock_time']-transaction['text']['txs'][0]['block_height']
    if AbsoluteUnlock==60 or AbsoluteUnlock==59:
      myTx['priority']="high"
    elif AbsoluteUnlock==180 or AbsoluteUnlock==179:
      myTx['priority']="medium"
    elif AbsoluteUnlock==540 or AbsoluteUnlock==539:
      myTx['priority']="normal"
    elif AbsoluteUnlock==1620 or AbsoluteUnlock==1619:
      myTx['priority']="low"
    

    if 'rct_signatures' in transactionJson:
      rctSig=transactionJson['rct_signatures']
      if 'txnFee' in rctSig:
        myTx['txnFee']=transactionJson['rct_signatures']['txnFee']
      if 'txnFee_usd' in rctSig:
        myTx['txnFee_usd']=transactionJson['rct_signatures']['txnFee_usd']
      if 'txnOffshoreFee' in rctSig:
        myTx['txnOffshoreFee']=transactionJson['rct_signatures']['txnOffshoreFee']
      if 'txnOffshoreFee_usd' in rctSig:
        myTx['txnOffshoreFee_usd']=transactionJson['rct_signatures']['txnOffshoreFee_usd']

    myTx['block_height']=transaction['text']['txs'][0]['block_height']
    myTx['block_timestamp']=datetime.utcfromtimestamp(transaction['text']['txs'][0]['block_timestamp'])
    myTx['_id']=tx
    return myTx
  
  def getInfo(self):
    return self.callDeamonJsonRPC("GET","get_info")
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
    try:
      if data:
        response = requests.request(verb, self.url + "/" + query, data=json.dumps(data), headers=headers, timeout=2)
      else:
        response = requests.request(verb, self.url + "/" + query, headers=headers, timeout=2)
      callback['status_code']=response.status_code
    except requests.exceptions.Timeout:
      print ("Timeout on BC node")
      pass

    try:
      if 'test' in response:
        extract=re.sub('signature": ".*[^a-zA-Z0-9].*",','signature": "",',response.text)
        callback['text']=json.loads(extract)
    except Exception as e:
      print (e)
      print (response.text)
      print (extract)
      callback['text']=response.text
    
    return callback