from blockchain import blockchain
from coingecko import coingecko

def importExchangePrice():
  Coingecko=coingecko()
  Coingecko.importExchangePrice(1)


def batch():
  Blockchain=blockchain()
  Blockchain.importCurrencies()
  importExchangePrice()
  Blockchain.scanBlockchain()
  
batch()