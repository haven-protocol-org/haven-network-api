import datetime
from blockchain import blockchain
from coingecko import coingecko

def importExchangePrice(duration):
  Coingecko=coingecko()
  Coingecko.importExchangePrice(duration)


def batch():
  Blockchain=blockchain()
  Blockchain.importCurrencies()
  importExchangePrice(365*3)
  importExchangePrice(90)
  importExchangePrice(2)
  Blockchain.scanBlockchain()

begin_time = datetime.datetime.now()
batch()
time_elapsed = datetime.datetime.now() - begin_time
print("Script ended in " + str(time_elapsed))