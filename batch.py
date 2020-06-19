import datetime
from blockchain import blockchain
from coingecko import coingecko

def importExchangePrice():
  Coingecko=coingecko()
  Coingecko.importExchangePrice(90)


def batch():
  #Blockchain=blockchain()
  #Blockchain.importCurrencies()
  importExchangePrice()
  #Blockchain.scanBlockchain()

begin_time = datetime.datetime.now()
batch()
time_elapsed = datetime.datetime.now() - begin_time
print("Script ended in " + str(time_elapsed))